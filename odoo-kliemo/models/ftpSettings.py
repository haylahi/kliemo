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
    directory_poa = fields.Char(String="POA Directory", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    directory_asn = fields.Char(String="ASN Directory", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    directory_stock = fields.Char(String="STOCK Report Directory", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    active = fields.Boolean(String="Active", required=False)
    frequency = fields.Integer(String="Frequency (hours)", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    job_id = fields.One2many('kliemo_orders_parser.job', 'settings_id', string="Jobs")
    input_picking_type = fields.Many2one('stock.picking.type', string="IN Picking Type", required=True, states={STATE_NEW: [('readonly', False)],}, readonly=True)
    delivery_method = fields.Selection([('initial', 'initial'), ('subsequent', 'subsequent'), ('both', 'Initial/subsequent')], string="Delivery Method", required=True)
    service_provider = fields.Char(string="Service Provider")
    service_type = fields.Selection([('print', 'print'), ('warehouse', 'warehouse'), ('external', 'external')], string="Service Type", required=True)
    manager_user = fields.Many2many('res.partner', string="Managers", required=True, readonly=False)
    last_execution_date = fields.Datetime(string="Last Executed")
    state = fields.Selection([(STATE_NEW, STATE_NEW), (STATE_RUNNING, STATE_RUNNING)], default=STATE_NEW, String="State")
    passed_test = fields.Boolean(string="Test passed", default=False)

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
        try:
            ftp.rename(original_path, destination_path)
        except Exception, e:
            _logger.debug("Error while moving file (%s) on FTP server, so delete it", original_path)
            ftp.delete(original_path)

    @api.multi
    def unzip_file(self, ftp, f):
        pass

    @api.multi
    def zip_file(self, ftp, f):
        pass        

    # -----------------------------------------------------------------------
    # METHOD ACTIONS TRIGERRED BY BUTTONS
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

    @api.multi
    def action_create_stockreport(self):
        self.create_and_upload_stock_report()

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
    def create_and_upload_stock_report(self):
        """
        This method will create the stock report at the given time
        and will save it as a File in the system then open it
        """
        
        cr = self.env.cr
        uid = self.env.user.id

        _logger.debug("Create A Stock Report")

        try:
            # ---- STOCK
            nsmap = {
                None:'http://www.crossmediasolutions.de/GPN/springer/po-1.9',
                "xsi":"http://www.w3.org/2001/XMLSchema-instance",
                     }
            stockxml = etree.Element("stock_report", nsmap=nsmap)
            stockxml.attrib['{{{pre}}}schemaLocation'.format(pre="http://www.w3.org/2001/XMLSchema-instance")] =  "http://www.crossmediasolutions.de/GPN/springer/po-1.9 http://www.springer.com/schemas/stock-report/1.0 StockReport.xsd"

            # ---- STOCK-HEADER
            stockHeader = etree.SubElement(stockxml, "header")

            node = etree.Element("datetime")
            node.text = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S %Z")
            stockHeader.append(node)
            node = etree.Element("vendor")
            node.text = 'kliemo warehouse'
            stockHeader.append(node)
            # ----

            # ---- STOCK
            stockItem = etree.SubElement(stockxml, "stock")

            # Take all products.products that are set as 'magazine'
            products_obj = self.pool.get('product.template')
            products_id = products_obj.search(cr, uid, [('is_magazine', '=', True)])
            for magazine in products_obj.browse(cr, uid, products_id):
                # Get Issues
                for issue in magazine.product_variant_ids:
                    # Issue
                    item = etree.Element('issue')
                    # Journal ID
                    node = etree.SubElement(item, 'journal_id')
                    node.text = str(issue.journal_id)
                    # Volume ID
                    node = etree.SubElement(item, 'volume_id')
                    node.text = str(issue.issue_volume)
                    # Issue ID
                    node = etree.SubElement(item, 'issue_id_start')
                    node.text = str(issue.issue_number)
                    # Type
                    node = etree.SubElement(item, 'type')
                    node.text = 'supplement' if issue.issue_type == 'special' else issue.issue_type # error between 'supplement' and 'special'
                    # Quantity
                    node = etree.SubElement(item, 'quantity')
                    node.text = str(int(issue.qty_available))
                    # Owner 
                    node = etree.SubElement(item, 'Owner')
                    node.text = 'Springer'
                    stockItem.append(item)
            # ----

            # create string from XML
            content = etree.tostring(stockxml, pretty_print=True)

            timestamp = time.strftime("%Y-%m-%d_%H_%M_%S")

            # filename
            filename = "stockreport_kliemo_" + timestamp + ".xml"

            # create STOCK file
            file_id = self.pool.get('kliemo_orders_parser.file').create(cr, uid, {
                'type': File.TYPESTOCK,
                'job_id': None,
                'creation_date': datetime.datetime.now(),
                'name': filename,
                'content': content,
                'state': File.STATE_DONE,
            })

            self.upload_files([file_id], File.TYPESTOCK)

        except Exception, e:
            raise osv.except_osv(_("Error while creating and uploading the Stock Report!"), _("Here is what we got instead:\n %s") % tools.ustr(e))

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

    @api.multi
    def upload_files(self, file_ids, file_type):
        """
        This function will zip given files (and encapsulate them as 'POA' or 'ASN' depending on their type) and upload them to the FTP server
        """
        cr = self.env.cr
        uid = self.env.user.id

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")

        zipfilename = ''
        server_path = ''
        tmp_zipfilename = ''
        zipfile_folder = None
        if file_type == File.TYPEPOA:
            zipfilename = 'poa_mps_' + timestamp + '.zip'
            server_path = self.directory_poa
            tmp_zipfilename = '/home/kliemo/springer_files/' + zipfilename
            zipfile_folder = zipfile.ZipFile(tmp_zipfilename, 'w')

        elif file_type == File.TYPEASN:
            zipfilename = 'asn_mps_' + timestamp + '.zip'
            server_path = self.directory_asn
            tmp_zipfilename = '/home/kliemo/springer_files/' + zipfilename
            zipfile_folder = zipfile.ZipFile(tmp_zipfilename, 'w')

        elif file_type == File.TYPESTOCK:
            zipfilename = 'stockreport_' + timestamp + '.xml'
            server_path = self.directory_stock
            tmp_zipfilename = '/home/kliemo/springer_files/' + zipfilename
            zipfile_folder = open(tmp_zipfilename, 'w')
        
        for file_id in file_ids:
            file_to_save = self.pool.get('kliemo_orders_parser.file').browse(cr, uid, file_id)
            if not file_to_save:
                _logger.debug("Error, this file: %s has not been got in DB", file_id)
                continue
            if file_type == File.TYPEPOA or file_type == File.TYPEASN:
                _logger.debug("will add file '%s' to zip %s", file_to_save.name, tmp_zipfilename)
                zipfile_folder.writestr(file_to_save.name, file_to_save.content.encode('utf-8'))
                _logger.debug("file added to zip")
            elif file_type == File.TYPESTOCK:
                zipfile_folder.write(file_to_save.content.encode('utf-8'))
                _logger.debug("File written")

        _logger.debug("close zipfile (or file)")
        #poalist = len(zipfile_folder.infolist())
        zipfile_folder.close()

        # connect the ftp
        ftp = self.connect()

        _logger.debug("server_path: %s", server_path)
        complete_path = server_path + zipfilename
        _logger.debug("will upload zipfile to %s", complete_path)
            
        zipfilebin = open(tmp_zipfilename,'rb')
        self.write_file(ftp, complete_path , zipfilebin.read())
        _logger.debug('file uploaded')

        _logger.debug("delete zipfile")
        os.remove(tmp_zipfilename)

        # sleep a bit in order to not write again on the files
        time.sleep(0.5)

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

    def cron_get_asn_and_upload(self, cr, uid, ids=None, context=None):
        """
        Executed by cron
        Upload all ASN files on FTP for the next day
        """

        _logger.debug("Send ASN files")
        ftps = self.pool.get('kliemo_orders_parser.ftpsettings').search(cr, uid, [('active','=',True)])
        for ftp_id in ftps:
            ftp = self.pool.get('kliemo_orders_parser.ftpsettings').browse(cr, uid, ftp_id)

            asn_files = []
            for job in ftp.job_id:
                if job.date >= datetime.datetime.strftime(datetime.datetime.now().date()+ datetime.timedelta(days=-1),"%Y-%m-%d %H:%M:%S") and job.date <= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
                    asn_files = self.pool.get('kliemo_orders_parser.file').search(cr, uid, [
                        ('creation_date', '>=', datetime.datetime.strftime(datetime.datetime.now().date()+ datetime.timedelta(days=-1),"%Y-%m-%d %H:%M:%S")),
                        ('creation_date', '<=', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        ('type', '=', File.TYPEASN),
                        ('job_id','=',job.id)])
                    _logger.debug("File ids: %s", asn_files)
                
                if len(asn_files) > 0:
                    ftp.upload_files(asn_files, File.TYPEASN)

    def cron_create_stock_report_and_upload(self, cr, uid, ids=None, context=None):
        """
        Executed by cron
        gets a stock XML report and uploads it to the server
        """

        _logger.debug("Get Stock XML Report")

        ftps = self.pool.get('kliemo_orders_parser.ftpsettings').search(cr, uid, [('active','=',True)])
        for ftp_id in ftps:
            ftp = self.pool.get('kliemo_orders_parser.ftpsettings').browse(cr, uid, ftp_id)
            ftp.create_and_upload_stock_report()
        
        