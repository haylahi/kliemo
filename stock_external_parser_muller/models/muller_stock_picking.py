# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp import models, fields, api
import logging
from openerp.osv import osv

class MullerStockPicking(models.Model):
    _inherit = ['stock.picking']

    delivery_type = fields.Selection([('germany', 'Inland'), ('row', 'Ausland')], string="Delivery Type")
    