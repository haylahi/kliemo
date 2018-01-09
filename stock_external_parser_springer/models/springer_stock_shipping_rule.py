# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models, fields, api
_logger = logging.getLogger(__name__)

class SpringerShippingRule(models.Model):
    _inherit = ['stock.shipping_rule']

    used_for_springer = fields.Boolean(string="Used for Springer", default=False)
    shipping_method = fields.Selection([('standard', 'Standard'), ('courier', 'Courier'), ('consolidator', 'Collector')], string="Shipping method")
    delivery_method = fields.Selection([('initial', 'Initial Dispatch'), ('subsequent', 'Subsequent Delivery'), ('both', 'Both (initial and subsequent)')], string="Delivery method")
    po_box = fields.Char(string="PO-BOX")
    postal_permit = fields.Char(string="Postal Permit #")
    ads = fields.Char(string="ADS")
    phone = fields.Char(string="Phone")
    service = fields.Char(string="Service")
    pallet_number = fields.Char(string="Pallet #")
