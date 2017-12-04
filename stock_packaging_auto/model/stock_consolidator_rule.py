# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class consolidator_rule(models.Model):
    _name = 'stock.consolidator_rule'

    bin_number = fields.Char(string="Bin#", required=True)
    customer = fields.Char(string="Customer", required=True)
    customer_numbers = fields.Text(string="Customer No. (comma separated)")
    shipping_routine = fields.Selection([('daily', 'Daily'), ('twicy', 'Twice a week'), ('weekly', 'Weekly'), ('biweekly', 'Biweekly'), ('monthly', 'Monthly')], string="Shipping Routine", required=True)
    carrier = fields.Char(string="Carrier", required=True)
    comment = fields.Text(string="Remark")

    active = fields.Boolean(string="Active", default=True)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s | %s | %s" % (record.bin_number, record.customer, record.carrier)))
        return result