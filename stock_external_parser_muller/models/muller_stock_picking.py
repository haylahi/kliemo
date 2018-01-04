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
    country_id = fields.Many2one('res.country', compute='_compute_partner_country', store=True)

    @api.one
    @api.depends('partner_id')
    def _compute_partner_country(self):
        self.country_id = self.partner_id.country_id
            