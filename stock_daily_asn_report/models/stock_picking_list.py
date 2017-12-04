# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp.osv import orm

class stock_picking_list(orm.Model):
    _inherit = 'stock.picking'

    def _xls_all_pickings_report_fields(self, cr, uid, context=None):
        return [
            'external_order_number',
            'date',
            'asn_date',
            'tat',
            'product_quantity',
            'net_picking_weight',
            'total_picking_weight',
            'logistic_unit_quantity',
            'shipping_rule.code',
            'shipping_rule.label_number',
            'shipping_rule.service',
            'tracking_number',
            'partner_id.country_id.code',
            'partner_id.customer_number',
            'partner_id.name',
            'partner_id.street',
        ]

    def _xls_all_pickings_template(self, cr, uid, context=None):
        """
        Template updates

        """
        return {}
