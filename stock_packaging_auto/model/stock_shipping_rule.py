# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models, fields, api
_logger = logging.getLogger(__name__)

class shipping_rule(models.Model):
    _name = 'stock.shipping_rule'

    shipping_method = fields.Selection([('standard', 'Standard'), ('courier', 'Courier'), ('consolidator', 'Collector')], string="Shipping method", required=True)
    delivery_method = fields.Selection([('initial', 'Initial Dispatch'), ('subsequent', 'Subsequent Delivery'), ('both', 'Both (initial and subsequent)')], string="Delivery method", required=True)
    country = fields.Many2one('res.country', string="Country")
    region = fields.Many2one('res.country.group', string="Region")
    po_box = fields.Char(string="PO-BOX")
    postal_permit = fields.Char(string="Postal Permit #")
    ads = fields.Char(string="ADS")
    phone = fields.Char(string="Phone")
    weight_min = fields.Float(string="Min. weight", required=True)
    weight_max = fields.Float(string="Max. weight")
    weight_max_package = fields.Float(string="Max. weight/package")
    service = fields.Char(string="Service", required=True)
    label_number = fields.Integer(string="Label #")
    label_report = fields.Many2one('ir.actions.report.xml', string="Label report")
    pallet_number = fields.Char(string="Pallet #")
    code = fields.Char(string="Code")

    active = fields.Boolean(string="Active", default=True)
    priority = fields.Integer(string="Priority", help="The lower is the most prior")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.service
            if record.country:
                name += ", " + record.country.code
            if record.region:
                name += ":" + record.region.name
            result.append((record.id, name))
        return result
