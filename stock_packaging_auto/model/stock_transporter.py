# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models, fields, api
_logger = logging.getLogger(__name__)

class stock_transporter(models.Model):
    _name = 'stock.transporter'

    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    priority = fields.Integer(string="Priority")
    packages = fields.One2many('product.ul', 'transporter_id', string="Packages")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s" % (record.partner_id.name)))
        return result