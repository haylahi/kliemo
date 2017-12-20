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
    # MODEL FIELDS
    name = fields.Char(string="Name", required=True, states={'Inactive': [('readonly', False)],}, readonly=True)
    hostname = fields.Char(string="Hostname", required=True, states={'Inactive': [('readonly', False)],}, readonly=True)
    username = fields.Char(string="Username", required=True, states={'Inactive': [('readonly', False)],}, readonly=True)
    password = fields.Char(string="Password", required=True, states={'Inactive': [('readonly', False)],}, readonly=True)
    directory_in = fields.Char(string="Orders Directory", required=True, states={'Inactive': [('readonly', False)],}, readonly=True)
    directory_in_done = fields.Char(string="Done Orders Directory", states={'Inactive': [('readonly', False)],}, readonly=True, required=True)
    active = fields.Boolean(string="Active", required=False)
    frequency = fields.Integer(string="Frequency (hours)", required=True, states={'Inactive': [('readonly', False)],}, readonly=True)
    job_id = fields.One2many('kliemo_orders_parser.job', 'settings_id', string="Jobs")
    input_picking_type = fields.Many2one('stock.picking.type', string="IN Picking Type", required=True, states={'Inactive': [('readonly', False)],}, readonly=True)
    manager_user = fields.Many2many('res.partner', string="Managers", required=True, readonly=False)
    last_execution_date = fields.Datetime(string="Last Executed")
    state = fields.Selection([('Inactive', 'Inactive'), ('Confirmed', 'Confirmed')], string="State", default='Inactive', String="State")
    passed_test = fields.Boolean(string="Test passed", default=False)
    local_file_path = fields.Char(string="Local folder to store files", required=True)

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
            self.state = 'Confirmed'
        else:
            self.state = 'Inactive'
            raise osv.except_osv(_("Connection not tested."), _("Please test it before!"))

    @api.multi
    def action_reset_confirmation(self):
        self.state = 'Inactive'

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
            'status': 'Waiting'
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
        file_names = self.list_file(ftp)
        _logger.debug("Files: %s", file_names)
        # Files: ['foo.zip']

        number_of_fetched_files = 0
        # For each zip file in the ftp folder
        for my_file in file_names:
            # Test if it is the 'done' or 'test' folder
            if my_file == "done" or my_file == "test":
                continue
            # Limit tested here
            if number_of_fetched_files == limit:
                break

            tmp_filename = self.local_file_path + my_file
            file_content = self.read_file(ftp, my_file)

            _logger.debug('download zip to %s', tmp_filename)

            fo = open(tmp_filename, 'wb')
            fo.write(file_content)
            fo.close()

            zfile = zipfile.ZipFile(tmp_filename)
            _logger.debug("zip_file.namelist(): {}".format(zfile.namelist()))
            # zip_file.namelist(): ['ZBH_2018001_Teil 2 INland Pakte***.xml']
            dir_name = tmp_filename.replace('.zip', '')
            # dir_name = str(self.local_file_path + file).replace('.zip', '')
            if not os.path.exists(dir_name):
                _logger.debug("Create directory: %s", dir_name)
                os.mkdir(dir_name)
                if not os.path.exists(dir_name):
                    _logger.debug("ERROR ERROR DIRECTORY NOT CREATED")
            for name in zfile.namelist():
                # Extract zip content dir_name
                _logger.debug("Decompressing " + name + " on " + dir_name)
                zfile.extract(name, dir_name)
                _logger.debug("ZIP extracted")
                complete_file_name = os.path.join(dir_name, name)
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
                        'type': 'IN',
                        'state': 'New',
                })
                _logger.debug("Create entry with file_id: [{}]".format(file_id))

                po_file_ids.append(file_id)
                number_of_fetched_files = number_of_fetched_files + 1

                # Delete the PO file on server and tmp
                # os.remove(complete_file_name)
                #_logger.debug("Clean up up work dir")
                # removing the TMP file is done in the job code because it allows for keeping in case of problem
                # Move file in 'done' folder
            _logger.debug("Clean up up work dir")
            self.move_file(ftp, my_file, self.directory_in_done + my_file)
            
        #shutil.rmtree(dir_name)

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
        settings_ids = settings_obj.search(cr, uid, [('active', '=', True), ('state', '=', 'Confirmed')])
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
        
        