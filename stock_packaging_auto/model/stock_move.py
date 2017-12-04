# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class stock_move(models.Model):
    _inherit = ['stock.move']

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s | %sx %s, %s-%s" % (record.picking_id.external_order_number, record.product_uom_qty, record.product_id.name, record.product_id.issue_volume, record.product_id.issue_number)))
        return result