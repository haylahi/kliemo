# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models, fields, api
_logger = logging.getLogger(__name__)

class shipping_rule(models.Model):
    _name = 'stock.shipping_rule'

    name = fields.Char(string="Name")
    country = fields.Many2one('res.country', string="Country")
    region = fields.Many2one('res.country.group', string="Region")
    weight_min = fields.Float(string="Min. weight", required=True)
    weight_max = fields.Float(string="Max. weight")
    weight_max_package = fields.Float(string="Max. weight/package")
    label_number = fields.Integer(string="Label #")
    label_report = fields.Many2one('ir.actions.report.xml', string="Label report")
    code = fields.Char(string="Code")
    active = fields.Boolean(string="Active", default=True)
    priority = fields.Integer(string="Priority", help="The lower is the most prior")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = str(self.name)
            if record.country:
                name += ", " + str(record.country.code)
            if record.region:
                name += ":" + str(record.region.name)
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
            return super(shipping_rule, self).name_search(name, args, operator, limit)
        args = args or []
        domain = ['|', ('code', operator, name), ('name', operator, name)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()
