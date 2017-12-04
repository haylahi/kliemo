# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
import time
from openerp import models, fields
_logger = logging.getLogger(__name__)

class stock_shipping_box(models.Model):
    _name = 'stock.shipping_box'

    transporter = fields.Many2one('stock.transporter', string="Transporter")
    tracking_number = fields.Char(string="Box tracking number")
    date_sent = fields.Datetime(string="Date sent")
    picking_id = fields.Many2one('stock.picking', string="Picking List")
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], String="State")

    _defaults= {
        'date_sent': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }