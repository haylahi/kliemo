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


class MullerParser(models.Model):
    # parent generic parser
    _inherit = ['kliemo_orders_parser.ftpsettings']

    @api.model
    def _type_selection(self):
        selection = super(MullerParser, self)._type_selection()
        selection.append(('muller', 'Muller Verlag'))
        return selection

    type = fields.Selection(_type_selection, string='Type', required=True)
    
    report_to_email = fields.Char(string="Email(s) for report", states={'Inactive': [('readonly', False)],}, readonly=True)
