# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
import datetime
from lxml import etree
from xml.dom import minidom
import openerp.tools as tools
import logging
_logger = logging.getLogger(__name__)

class picking(models.Model):
    # -----------------------------------------------------------------------
    # MODEL INHERIT
    _inherit = ['stock.picking']
    _order = 'date desc'

    # -----------------------------------------------------------------------
    # MODEL FIELDS
    file_id = fields.Many2one('kliemo_orders_parser.file', string="XML File")
    settings_id = fields.Many2one(related='file_id.job_id.settings_id', string="Setting")
    settings_type = fields.Selection(related='file_id.job_id.settings_id.type', string="Setting type")
    external_order_number = fields.Char(string="Order number")
