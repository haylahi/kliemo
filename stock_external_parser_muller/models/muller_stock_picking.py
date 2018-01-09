# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp import models, fields, api
import logging
from openerp.osv import osv
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

class MullerStockPicking(models.Model):
    _inherit = ['stock.picking']

    delivery_type = fields.Selection([('germany', 'Inland'), ('row', 'Ausland')], string="Delivery Type")
    country_id = fields.Many2one('res.country', compute='_compute_partner_country', store=True)

    @api.one
    @api.depends('partner_id')
    def _compute_partner_country(self):
        self.country_id = self.partner_id.country_id

    # This method will fetch the correct shipping rule for the current picking list
    @api.multi
    def compute_shipping(self):
        for picking in self:
            # If not Springer, pass to the upper level
            if picking.settings_id.type != 'muller':
                super(MullerStockPicking, picking).compute_shipping()
                continue

            # init
            picking._compute_gross_weight()
            picking.compute_packaging()
            picking.logistic_unit_quantity = 0
            picking.shipping_rule = None
            picking.logistic_unit_report = None

            if picking.delivery_type == 'row':
                picking.shipping_rule = False
                picking.logistic_unit_report = False


            # get shipping rules
            rules_obj = self.pool.get('stock.shipping_rule')
            rules = rules_obj.search(self.env.cr, self.env.uid, [('used_for_muller', '=', True)], order='priority asc')

            # error, no rules
            if len(rules) < 1:
                raise osv.except_osv(_("Error"), _("There is no shipping rules defined!"))

            filter = []

            # loop on rules to get the ruled countries and country groups
            countries_ruled = []
            country_groups_rules = []
            for rule in rules_obj.browse(self.env.cr, self.env.uid, rules):
                if rule.country != None and rule.country.id not in countries_ruled:
                    countries_ruled.append(rule.country.id)
                if rule.region != None and rule.region.id not in country_groups_rules:
                    country_groups_rules.append(rule.region.id)
            _logger.debug("Countries ruled: %s", countries_ruled)
            _logger.debug("Groups of countries ruled: %s", country_groups_rules)

            # check country
            if picking.partner_id.country_id.id in countries_ruled:
                filter.append('|')
                filter.append(['country', '=', picking.partner_id.country_id.id])
                filter.append(['country', '=', False])
            # check for europe
            else:
                if len(countries_ruled) > 0:
                    regions_obj = self.pool.get('res.country.group')
                    regions_id = regions_obj.search(self.env.cr, self.env.uid, [])
                    region_match = False
                    for region in regions_obj.browse(self.env.cr, self.env.uid, regions_id):
                        if picking.partner_id.country_id in region.country_ids:
                            region_match = True
                            filter.append(['region', '=', region.id])
                    # Measns that the country is in ROW
                    if not region_match:
                        filter.append(['region', '=', 'ROW'])

            # Only the rules used for Muller
            filter.append(['used_for_muller', '=', True])

            _logger.debug("Filter: %s", filter)

            rules = rules_obj.search(self.env.cr, self.env.uid, filter, order='priority asc')

            # loop on all rules to find the right one
            for rule in rules_obj.browse(self.env.cr, self.env.uid, rules):
                _logger.debug("Rule: %s - %s", rule.label_number, rule.service)
                # Issues Max
                if rule.max_issues_per_shipping != 0 and rule.max_issues_per_shipping < picking.product_quantity:
                    _logger.debug("Too much issues for this rule")
                    continue

                if picking.net_picking_weight != 0 and rule.weight_max != 0 and picking.net_picking_weight > rule.weight_max:
                    _logger.debug("Weight too much")
                    continue

                if picking.net_picking_weight != 0 and picking.net_picking_weight < rule.weight_min:
                    _logger.debug("Weight too low")
                    continue

                _logger.debug("Rule found: %s", rule.service)

                # Number of packages
                if rule.weight_max_package > 0 and rule.weight_max_package < picking.net_picking_weight:
                    picking.logistic_unit_quantity = int((picking.net_picking_weight / rule.weight_max_package) + 1)
                else:
                    picking.logistic_unit_quantity = 1

                #  Report
                picking.shipping_rule = rule
                picking.logistic_unit_report = rule.label_report
                break

            # Create the boxes
            if len(picking.boxes) < picking.logistic_unit_quantity:
               i = 1
               while i <= picking.logistic_unit_quantity:
                    self.pool.get('stock.shipping_box').create(self.env.cr, self.env.uid, {
                        'picking_id': picking.id,
                        'state': 'draft',
                    })
                    i += 1

            if not picking.shipping_rule:
                raise osv.except_osv(_("Error"), _("MULER ! There is no shipping rule that matches this picking list!"))
            