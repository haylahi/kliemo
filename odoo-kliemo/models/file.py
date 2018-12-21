# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp.addons.document.document import nodefd_static
from thread import _local
from openerp import models, fields, api
from lxml import etree
from xml.dom import minidom
import openerp.tools as tools
from openerp.osv import osv
from openerp.tools.translate import _
import datetime
from zipfile import ZipFile
import os
import time
import logging
from openerp.osv import osv
_logger = logging.getLogger(__name__)


# MODEL USED FOR MULTIPLE UPLOAD
class file_multiple_upload(osv.osv_memory):
    _name = "kliemo_orders_parser.file.multiple.upload"
    _description = "File Multiple Upload"

    def upload_multiple_files(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids', []) or []

        files_to_upload = []
        file_obj = self.pool.get('kliemo_orders_parser.file')

        # get the file type of the first file
        first = file_obj.browse(cr, uid, active_ids[0])
        file_type = first.type

        # Filter on files regarding type (no upload of IN files, and check if all same type)
        for f in file_obj.browse(cr, uid, active_ids):
            
            if f.type != 'in' and f.type == file_type:
                files_to_upload.append(f.id)

        if len(files_to_upload) > 0:
            try:
                settings_obj = self.pool.get('kliemo_orders_parser.ftpsettings')
                settings_ids = settings_obj.search(cr, uid, [('active', '=', True), ('state', '=', 'Confirmed')])
                setting = settings_obj.browse(cr, uid, settings_ids)
                setting = setting[0]

                if setting != None:
                    setting.upload_files(files_to_upload, file_type)
                else:
                    raise Exception("No Setting active found tu upload the file")
            except Exception, e:
                raise osv.except_osv(_("(file.upload) Multiple upload file failed."), _("Here is the error:\n %s") % tools.ustr(e))


# FILE MODEL, USED TO STORE INFO FROM AND TO XML
class File(models.Model):
    # -----------------------------------------------------------------------
    # MODEL NAME
    _name = 'kliemo_orders_parser.file'
    _order = 'creation_date desc'

    # -----------------------------------------------------------------------
    # MODEL FIELDS
    creation_date = fields.Datetime(String="Creation date", required=True)
    name = fields.Char(String="Name", required=True)

    @api.model
    def _type_selection(self):
        return [('IN', 'In')]
    type = fields.Selection(_type_selection, string='Type', required=True)
    state = fields.Selection([('New', 'New'), ('Running', 'Running'), ('Parsing Error', 'Parsing Error'), ('Parsed', 'Parsed'), ('cancel', 'Cancelled')], default='New', String="State")
    content = fields.Text(String='Content')
    job_id = fields.Many2one('kliemo_orders_parser.job', ondelete='cascade', string="Job")
    settings_id = fields.Many2one(related='job_id.settings_id', string="Setting")
    exceptions = fields.One2many('kliemo_orders_parser.exception', 'file_id', string="Exceptions")
    exceptions_quantity = fields.Integer(string="Number of exceptions", store=False, compute="_compute_number_of_exceptions")

    # -----------------------------------------------------------------------
    # COMPUTE METHODS
    @api.multi
    @api.onchange('exceptions')
    def _compute_number_of_exceptions(self):
        self.exceptions_quantity = len(self.exceptions)

    # -----------------------------------------------------------------------
    # METHOD ACTIONS TRIGERRED BY BUTTONS
    @api.multi
    def action_set_as_error(self):
        self.setAsError()

    @api.multi
    def action_unset_as_error(self):
        self.setAsErrorFixed()

    @api.multi
    def action_parse(self):
        self.parse_again()

    @api.multi
    def action_upload(self):
        self.upload()

    # -----------------------------------------------------------------------
    # ODOO INHERIT METHODS

    # -----------------------------------------------------------------------
    # MODEL METHODS
    @api.multi
    def setAsError(self):
        self.state = 'Parsing Error'
        self.job_id.setAsError()

    @api.multi
    def setAsErrorFixed(self):
        for exc in self.exceptions:
            if exc.state == 'Waiting for fix' and exc.level == "High":
                self.state = 'Parsing Error'
                self.job_id.setAsError()
                return
        self.state = 'Parsed'
        self.job_id.setAsErrorFixed()

    # Used as an Interface
    @api.multi
    def parse_again(self):
        return True

    # Used as an Interface
    @api.multi
    def parse_again(self):
        return True

    @api.multi
    def upload(self):
        # We never upload back IN files
        if self.type != 'in':
            try:
                files_to_upload = [self.id]
                setting = None
                if self.job_id:
                    if self.job_id.settings_id:
                        self.job_id.settings_id.upload_files(files_to_upload, self.type)
                    else:
                        raise Exception("No Setting found on the job linked to this file to upload the file")
                else:
                    raise Exception("No Job found on the file to upload the file")
            except Exception, e:
                raise osv.except_osv(_("(file.upload) Upload file failed for %s") % self.name, _("Here is the error:\n %s") % tools.ustr(e))

    @api.multi
    def createAnException(self, message, level, picking_id):
        """
        This method creates an exception using the message, level and picking id given
        """
        cr = self.env.cr
        uid = self.env.user.id

        exception_id = self.pool.get('kliemo_orders_parser.exception').create(cr, uid, {
            'message': message,
            'file_id': self.id,
            'level': level,
            'picking_list_id': picking_id,
            'state': 'Waiting for fix',
        })

        if (level == 'High'):
            self.setAsError()
            self.pool.get('kliemo_orders_parser.exception').browse(cr, uid, exception_id).sendEmailToManager()
        return exception_id

    # -----------------------------------------------------------------------
    # CRON METHODS
    def cron_delete_old_files(self, cr, uid, ids=None, context=None):
        """
        Method that will be excecuted by the cron task
        """
        format = "%Y-%m-%d %H:%M:%S"

        # Get all files
        files_obj = self.pool.get('kliemo_orders_parser.file')
        now = datetime.datetime.now().date()
        enddate = now + datetime.timedelta(days=-30)
        enddate = datetime.datetime.strftime(enddate, "%Y-%m-%d %H:%M:%S")
        _logger.debug("enddate is {}".format(enddate))
        files_ids = files_obj.search(cr, uid, [('creation_date', '<'
                                                                 '=', enddate)])
        for file_id in files_ids:
            file = files_obj.browse(cr, uid, file_id)
            file.unlink()
        _logger.debug('{} files deleted'.format(len(files_ids)))

    # -----------------------------------------------------------------------
    # UTILITIES METHODS
    def getNumberOfItems(self, dom, nodeName):
        element = dom.getElementsByTagName(nodeName)
        return len(element)

    @staticmethod
    def getNodeValueIfExists(dom, nodeName):
        """
        This method gets the dom XML value for nodeName if it exists
        """
        if dom:
            element = dom.getElementsByTagName(nodeName)
            if element:
                if len(element) == 1:
                    element_0 = element[0]
                    if element_0.firstChild:
                        child = element_0.firstChild
                        if child.nodeValue:
                            value = child.nodeValue
                            if value:
                                try:
                                    value = str(value)
                                    return value
                                except UnicodeError:
                                    value =  value.encode('utf-8')
                                    return value
                                else:
                                    return unicode(value, "ascii")
                                    pass
        _logger.debug("return None")
        return ""

    def removeGermanSpecialChars(self, string):
        string = string.replace("ë", "e")
        string = string.replace("Ë", "E")
        string = string.replace("ö", "oe")
        string = string.replace("Ö", "OE")
        string = string.replace("ü", "u")
        string = string.replace("Ü", "u")
        string = string.replace("ä", "ae")
        string = string.replace("Ä", "AE")
        string = string.replace("'", "")
        string = string.replace('"', "")
        return string
        
