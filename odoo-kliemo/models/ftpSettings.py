# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from ftplib import FTP
import logging, os
import StringIO
import datetime
import job
from file import File
from lxml import etree
from xml.dom import minidom
from zipfile import ZipFile
import zipfile
import time
import shutil

from openerp.tools.translate import _
import openerp.tools as tools

_logger = logging.getLogger(__name__)

class ftpSettings(models.Model):
    # -----------------------------------------------------------------------
    # MODEL NAME
    _name = 'kliemo_orders_parser.ftpsettings'

    # -----------------------------------------------------------------------
    # STATES DICTIONARY
    STATE_NEW = "Inactive"
    STATE_RUNNING = "Confirmed"

    # -----------------------------------------------------------------------
    # MODEL FIELDS
    name = fields.Char(String="Name", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    hostname = fields.Char(String="Hostname", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    username = fields.Char(String="Username", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    password = fields.Char(String="Password", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    directory_in = fields.Char(String="Orders Directory", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    active = fields.Boolean(String="Active", required=False)
    frequency = fields.Integer(String="Frequency (hours)", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    job_id = fields.One2many('kliemo_orders_parser.job', 'settings_id', string="Jobs")
    input_picking_type = fields.Many2one('stock.picking.type', string="IN Picking Type", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    manager_user = fields.Many2many('res.partner', string="Managers", required=True, readonly=False)
    last_execution_date = fields.Datetime(string="Last Executed")
    state = fields.Selection([(STATE_NEW, STATE_NEW), (STATE_RUNNING, STATE_RUNNING)], default=STATE_NEW, String="State")
    passed_test = fields.Boolean(string="Test passed", default=False)

    @api.model
    def _type_selection(self):
        return [('unknown', 'Unknown')]
    type = fields.Selection(_type_selection, string='Type', required=True)

    # -----------------------------------------------------------------------
    # FTP SYSTEM METHODS
    @api.multi
    def connect(self):
        ftp = FTP(self.hostname, self.username, self.password)
        ftp.cwd(self.directory_in)
        return ftp

    @api.multi
    def close(self, ftp):
        ftp.close()

    # retrun the filename in a list
    @api.multi
    def list_file(self, ftp):
        return ftp.nlst()

    @api.multi
    def read_file(self, ftp, filename):
        data = StringIO.StringIO()
        ftp.retrbinary("RETR " + filename, data.write)
        return data.getvalue()

    @api.multi
    def write_file(self, ftp, filename, filecontent):
        ftp.storbinary("STOR " + filename, StringIO.StringIO(filecontent))

    @api.multi
    def delete_file(self, ftp, filename):
        ftp.delete(filename)

    @api.multi
    def move_file(self, ftp, original_path, destination_path):
        ftp.rename(original_path, destination_path)

    @api.multi
    def unzip_file(self, ftp, f):
        pass

    @api.multi
    def zip_file(self, ftp, f):
        pass        

    # -----------------------------------------------------------------------
    # METHOD ACTIONS TRIGERED BY BUTTONS
    @api.multi
    def action_test_ftp_server(self):
        try:
            ftp = self.connect()
        except Exception, e:
            self.passed_test = False
            raise osv.except_osv(_("Connection Test Failed!"), _("Here is what we got instead:\n %s") % tools.ustr(e))
        finally:
            try:
                if ftp:
                    self.close(ftp)
            except Exception:
                pass
        self.passed_test = True

    @api.multi
    def action_create_job(self):
        self.create_job()

    @api.multi
    def action_confirm_ftp_server(self):
        if self.passed_test:
            self.state = ftpSettings.STATE_RUNNING
        else:
            self.state = ftpSettings.STATE_NEW
            raise osv.except_osv(_("Connection not tested."), _("Please test it before!"))

    @api.multi
    def action_reset_confirmation(self):
        self.state = ftpSettings.STATE_NEW

    # -----------------------------------------------------------------------
    # ODOO INHERIT METHODS
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s - %s@%s" % (record.name, record.username, record.hostname)))
        return result
    
    # -----------------------------------------------------------------------
    # MODEL METHODS
    @api.multi
    def create_job(self):
        """
        This methods creates a job for the setting and returns its id
        """
        cr = self.env.cr
        uid = self.env.user.id
        job_id = self.pool.get('kliemo_orders_parser.job').create(cr, uid, {
            'date': datetime.datetime.now(),
            'settings_id': self.id,
            'status': job.job.STATUS_WAITING
                })
        return job_id

    @api.multi
    def download_files_and_save(self, job_id):
        """
        This method will connect to the FTP,
        List the files in the desired directory and download them,
        For each one, create a FILE in the system and return the recordset of the created FILEs

        I set a limit here to 150 files at the time, there as too much problem when more and possible TIMEOUTS in the FTP connection
        """
        limit = 150

        cr = self.env.cr
        uid = self.env.user.id

        po_file_ids = []

        # connect the ftp
        ftp = self.connect()

        # get file names
        filenames = self.list_file(ftp)
        _logger.debug("Files: %s", filenames)

        number_of_fetched_files = 0
        # For each zip file in the ftp folder
        for file in filenames:
            # Test if it is the 'done' or 'test' folder
            if file == "done" or file == "test":
                continue
            # Limit tested here
            if number_of_fetched_files == limit:
                break

            tmp_filename = '/home/kliemo/springer_files/' + file
            filecontent = self.read_file(ftp, file)

            # download Zipfile to /home/kliemo/springer_files/
            _logger.debug('download zip to %s', tmp_filename)
            fo = open(tmp_filename, 'wb')
            fo.write(filecontent)
            fo.close()

            zfile = zipfile.ZipFile(tmp_filename)
            _logger.debug("zfile.namelist(): %s", zfile.namelist())
            for name in zfile.namelist():
                # Extract zip content to /home/kliemo/springer_files/extracted/<file>/.
                (dirname, filename) = os.path.split(name)
                dirname = str('/home/kliemo/springer_files/extracted/' + file).replace('.zip', '')
                _logger.debug("Decompressing " + filename + " on " + dirname)
                if not os.path.exists(dirname):
                    _logger.debug("Create directory: %s", dirname)
                    os.mkdir(dirname)
                    if not os.path.exists(dirname):
                        _logger.debug("ERROR ERROR DIRECTORY NOT CREATED")
                zfile.extract(name, dirname)
                _logger.debug("ZIP extracted")

                complete_file_name = dirname + '/' + filename

                # Create order file
                _logger.debug("Open file: %s", complete_file_name)
                xml_string = open(complete_file_name)
                _logger.debug("File opened")
                data = StringIO.StringIO(xml_string.read()).getvalue()
                _logger.debug("File transformed to XML")

                file_id = self.pool.get('kliemo_orders_parser.file').create(cr, uid, {
                        'creation_date': datetime.datetime.now(),
                        'job_id': job_id,
                        'name': name,
                        'content': data,
                        'type': File.TYPEIN,
                        'state': File.STATE_NEW,
                })

                po_file_ids.append(file_id)

                # Delete the PO file on server and tmp
                shutil.rmtree(dirname)
                # removing the TMP file is done in the job code because it allows for keeping in case of problem
                # Move file in 'done' folder
                self.move_file(ftp, file, 'done/' + file)
                number_of_fetched_files = number_of_fetched_files + 1

        return po_file_ids

    

    # -----------------------------------------------------------------------
    # CRON METHODS
    def cron_ftp_file_getter(self, cr, uid, ids=None, context=None):
        """
        Method that will be excecuted by the cron task
        It creates a job and executes it (get files from FTP server, creates PL, post POA files in return)
        """
        _logger.debug("RUN CRON")
        # Get all FTP settings
        settings_obj = self.pool.get('kliemo_orders_parser.ftpsettings')
        settings_ids = settings_obj.search(cr, uid, [('active', '=', True), ('state', '=', ftpSettings.STATE_RUNNING)])
        for setting_id in settings_ids:
            # Get the setting
            setting = settings_obj.browse(cr, uid, setting_id)
            # Check last exectution date and frequency
            if not setting.last_execution_date:
                setting.last_execution_date = "1970-01-01 1:00:00"
            format = "%Y-%m-%d %H:%M:%S"
            time_delta = datetime.datetime.now() - datetime.datetime.strptime(setting.last_execution_date, format)
            # Execute
            time_delta_hours = int((time_delta.seconds / 3600)) + int((time_delta.days * 24))
            if time_delta_hours >= setting.frequency:
                _logger.debug("OK CREATE AND RUN JOB FOR FTP SETTING")
                new_job_id = setting.create_job()
                self.pool.get('kliemo_orders_parser.job').browse(cr, uid, new_job_id).run_job()
            else:
                _logger.debug("NOT THE MOMENT TO CREATE AND RUN A JOB")
        
        