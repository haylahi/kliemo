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
#import job
#from file import File
from lxml import etree
from xml.dom import minidom
from zipfile import ZipFile
import zipfile
import time
import shutil

from openerp.tools.translate import _
import openerp.tools as tools

_logger = logging.getLogger(__name__)

class SpringerParser(models.Model):
    # -----------------------------------------------------------------------
    # MODEL INHERIT
    _inherit = ['kliemo_orders_parser.ftpsettings']

    @api.model
    def _type_selection(self):
        selection = super(SpringerParser, self)._type_selection()
        selection.append(('springer', 'Springer Nature'))
        return selection

    type = fields.Selection(_type_selection, string='Type', required=True)

    directory_poa = fields.Char(String="POA Directory", states={'Inactive': [('readonly', False)],}, readonly=True)
    directory_asn = fields.Char(String="ASN Directory", states={'Inactive': [('readonly', False)],}, readonly=True)
    directory_stock = fields.Char(String="STOCK Report Directory", states={'Inactive': [('readonly', False)],}, readonly=True)
    delivery_method = fields.Selection([('initial', 'initial'), ('subsequent', 'subsequent'), ('both', 'Initial/subsequent')], string="Delivery Method")
    service_provider = fields.Char(string="Service Provider")
    service_type = fields.Selection([('print', 'print'), ('warehouse', 'warehouse'), ('external', 'external')], string="Service Type")

    @api.multi
    def action_create_stockreport(self):
        self.create_and_upload_stock_report()

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
                'type': 'STOCK',
                'job_id': None,
                'creation_date': datetime.datetime.now(),
                'name': filename,
                'content': content,
                'state': 'Parsed',
            })

            self.upload_files([file_id], 'STOCK')

        except Exception, e:
            raise osv.except_osv(_("Error while creating and uploading the Stock Report!"), _("Here is what we got instead:\n %s") % tools.ustr(e))

        # Set the file as uploaded
        file_id.uploaded = True

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
        if file_type == 'POA':
            zipfilename = 'poa_mps_' + timestamp + '.zip'
            server_path = self.directory_poa
            tmp_zipfilename = self.local_file_path + zipfilename
            zipfile_folder = zipfile.ZipFile(tmp_zipfilename, 'w')

        elif file_type == 'ASN':
            zipfilename = 'asn_mps_' + timestamp + '.zip'
            server_path = self.directory_asn
            tmp_zipfilename = self.local_file_path + zipfilename
            zipfile_folder = zipfile.ZipFile(tmp_zipfilename, 'w')

        elif file_type == 'STOCK':
            zipfilename = 'stockreport_' + timestamp + '.xml'
            server_path = self.directory_stock
            tmp_zipfilename = self.local_file_path + zipfilename
            zipfile_folder = open(tmp_zipfilename, 'w')

        for file_id in file_ids:
            file_to_save = self.pool.get('kliemo_orders_parser.file').browse(cr, uid, file_id)
            if not file_to_save:
                _logger.debug("Error, this file: %s has not been got in DB", file_id)
                continue
            if file_type == 'POA' or file_type == 'ASN':
                _logger.debug("will add file '%s' to zip %s", file_to_save.name, tmp_zipfilename)
                zipfile_folder.writestr(file_to_save.name, file_to_save.content.encode('utf-8'))
                _logger.debug("file added to zip")
            elif file_type == 'STOCK':
                zipfile_folder.write(file_to_save.content.encode('utf-8'))
                _logger.debug("File written")

        _logger.debug("close zipfile (or file) : %s", zipfile_folder)
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

        # Set files as uploaded
        for file_id in file_ids:
            file_to_save = self.pool.get('kliemo_orders_parser.file').browse(cr, uid, file_id)
            file_to_save.uploaded = True

        _logger.debug("delete zipfile")
        os.remove(tmp_zipfilename)

        # sleep a bit in order to not write again on the files
        time.sleep(0.5)

    def cron_get_asn_and_upload(self, cr, uid, ids=None, context=None):
        """
        Executed by cron
        Upload all ASN files on FTP for the next day
        """

        #_logger.debug("Send ASN files")
        ftps = self.pool.get('kliemo_orders_parser.ftpsettings').search(cr, uid, ['&', ('active','=',True), ('type', '=', 'springer')])
        if (len(ftps)) == 0:
            raise osv.except_osv(_("No parser for Springer is active"), _("You have to enable a parser for type 'springer' to do that"))
        for ftp_id in ftps:
            ftp = self.pool.get('kliemo_orders_parser.ftpsettings').browse(cr, uid, ftp_id)

            asn_files = self.pool.get('kliemo_orders_parser.file').search(cr, uid, [('uploaded', '=', False),
                    ('type', '=', 'ASN'),
                    ('settings_id','=', ftp.id)])
            _logger.debug("File ids: %s", asn_files)
            if len(asn_files) > 0:
                ftp.upload_files(asn_files, 'ASN')

    def cron_create_stock_report_and_upload(self, cr, uid, ids=None, context=None):
        """
        Executed by cron
        gets a stock XML report and uploads it to the server
        """

        _logger.debug("Get Stock XML Report")

        ftps = self.pool.get('kliemo_orders_parser.ftpsettings').search(cr, uid, ['&', ('active','=',True), ('type', '=', 'springer')])
        if (len(ftps)) == 0:
            raise osv.except_osv(_("No parser for Springer is active"), _("You have to enable a parser for type 'springer' to do that"))
        for ftp_id in ftps:
            ftp = self.pool.get('kliemo_orders_parser.ftpsettings').browse(cr, uid, ftp_id)
            ftp.create_and_upload_stock_report()