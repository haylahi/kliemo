# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class stock_logistic_unit(models.Model):
    _inherit = ['product.ul']

    weight_max = fields.Float(string="Maximum weight (Kg)")
    width_max = fields.Float(string="Maximum width (mm)")
    length_max = fields.Float(string="Maximum length (mm)")
    depth_max = fields.Float(string="Maximum depth (mm)")
    label_report = fields.Many2one('ir.actions.report.xml', string="Label report", index=True)
    sequence = fields.Integer(string="Sequence")
    transporter_id = fields.Many2one('stock.transporter', string="Transporter")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s (%s)" % (record.name, record.sequence)))
        return result