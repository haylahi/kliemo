# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from openerp import _
import logging
_logger = logging.getLogger(__name__)

class stock_picking_list(models.Model):
    _inherit = ['stock.picking']

    logistic_unit = fields.Many2one('product.ul', string="Packaging", index=True)
    logistic_unit_quantity = fields.Integer(string="Logistic units quantity", compute="_compute_number_of_boxes", default=1)
    logistic_unit_report = fields.Many2one('ir.actions.report.xml', string="Label", index=True, store=False, compute="_compute_label_report")
    packaging_sequence = fields.Integer(string="Packaging sequence", store=False, compute="_compute_packaging_sequence")

    printed = fields.Boolean(string="Printed", default=False)

    total_picking_weight = fields.Float(string="Gross Weight (Kg)", digits=(5, 3))
    net_picking_weight = fields.Float(string="Net Weight (Kg)", digits=(5, 3))
    tracking_number = fields.Char(string="Tracking number", compute="_compute_tracking_number")
    product_quantity = fields.Integer(string="Quantity of Products", store=False, compute="_compute_quantity_of_products")

    shipping_rule = fields.Many2one('stock.shipping_rule', string="Shipping rule")
    consolidator_rule = fields.Many2one('stock.consolidator_rule', string="Consolidator")

    # boxes
    boxes = fields.One2many('stock.shipping_box', 'picking_id', string="Shipping boxes")

    @api.one
    @api.onchange('boxes')
    def _compute_tracking_number(self):
        if len(self.boxes) < 1:
            self.tracking_number = "/"
        if len(self.boxes) == 1:
            if self.boxes[0] != None:
                self.tracking_number = str(self.boxes[0].tracking_number)
        else:
            tracking = ""
            for b in self.boxes:
                if b.tracking_number != None:
                    tracking += str(b.tracking_number) + ", "
            self.tracking_number = tracking

    @api.one
    @api.onchange('logistic_unit', 'shipping_rule')
    def _compute_label_report(self):
        #self.logistic_unit_report = self.logistic_unit.label_report
        self.logistic_unit_report = self.shipping_rule.label_report

    @api.one
    @api.onchange('boxes')
    def _compute_number_of_boxes(self):
        self.logistic_unit_quantity = len(self.boxes)

    @api.one
    @api.onchange('logistic_unit')
    def _compute_packaging_sequence(self):
        self.packaging_sequence = self.logistic_unit.sequence

    @api.one
    @api.onchange('move_lines')
    def _compute_quantity_of_products(self):
        nb = 0
        for line in self.move_lines:
            nb += line.product_uom_qty
        self.product_quantity = nb

    @api.one
    @api.onchange('move_lines')
    def _compute_gross_weight(self):
        computed_weight = 0
        for line in self.move_lines:
            computed_weight += (line.product_id.weight_net * line.product_uom_qty)

        self.net_picking_weight = computed_weight

    @api.multi
    def confirm_picking_list(self):
        if self.settings_type == 'springer':
            auto_set_ok = False
            # auto set rule
            if(self.file_id):
                try:
                    self.compute_packaging()
                    # auto set package
                    self.compute_shipping()
                    auto_set_ok = True
                except Exception, e:
                    _logger.debug("ERROR OF COMPUTING PACKAGING OR PICKING AUTO")
                    self.file_id.setAsError()

            # confirm the PL
            if auto_set_ok:
                self.action_confirm()
                self.action_assign()
                return self.print_list() # print the PL
        else:
            self.action_confirm()
            self.action_assign()
            return self.print_list() # print the PL
            

    @api.multi
    def set_smaller_package(self):
        packaging_obj = self.pool.get('product.ul')
        packagings = packaging_obj.search(self.env.cr, self.env.uid, [], order='sequence asc')
        if self.logistic_unit:
            packagings = packaging_obj.search(self.env.cr, self.env.uid, [('sequence', '<', self.packaging_sequence)], order='sequence desc')
        if packagings:
            for pack in packaging_obj.browse(self.env.cr, self.env.uid, packagings):
                self.logistic_unit = pack
                self.printed = False
                break
        else:
            raise osv.except_osv(_("Impossible"), _("The selected packaging is already the smallest one."))

    @api.multi
    def set_bigger_package(self):
        packaging_obj = self.pool.get('product.ul')
        packagings = packaging_obj.search(self.env.cr, self.env.uid, [], order='sequence desc')
        if self.logistic_unit:
            packagings = packaging_obj.search(self.env.cr, self.env.uid, [('sequence', '>', self.packaging_sequence)], order='sequence asc')
        if packagings:
            for pack in packaging_obj.browse(self.env.cr, self.env.uid, packagings):
                self.logistic_unit = pack
                self.printed = False
                break
        else:
            raise osv.except_osv(_("Impossible"), _("The selected packaging is already the biggest one."))

    @api.multi
    def print_list(self):
        return self.pool['report'].get_action(self.env.cr, self.env.uid, self.id, 'stock.report_picking', context=self.env.context)

    @api.multi
    def print_labels(self):
        _logger.debug('printing label')
        return self.pool['report'].get_action(self.env.cr, self.env.uid, self.id, 'stock_packaging_auto.base_label_report', context=self.env.context)

    @api.multi
    def compute_packaging(self):
        self._compute_gross_weight()

        # List available packages and find the one that matches our list
        packaging_obj = self.pool.get('product.ul')
        packagings = packaging_obj.search(self.env.cr, self.env.uid, [], order='sequence asc')
        if packagings:
            for pack in packaging_obj.browse(self.env.cr, self.env.uid, packagings):
                if (self.net_picking_weight <= pack.weight_max):
                    self.logistic_unit = pack
                    break

        if self.logistic_unit:
            # gross weight
            self.total_picking_weight = (self.logistic_unit_quantity * self.logistic_unit.weight) + self.net_picking_weight
        else:
            raise osv.except_osv(_("Error"), _("Can not get a packing automatically."))

    # This method will fetch the correct shipping rule for the current picking list
    @api.multi
    def compute_shipping(self):
        # init
        self._compute_gross_weight()
        self.compute_packaging()
        self.logistic_unit_quantity = 0
        self.shipping_rule = None
        self.logistic_unit_report = None

        if not self.file_id:
            raise osv.except_osv(_("Error"), _("Can not get auto shipping because this picking list is not linked to a  file."))

        # Shipping rule is 'consolidator'
        if self.shipping_method == 'consolidator':
            # Assign shipping rule
            rules_obj = self.pool.get('stock.shipping_rule')
            rules_id = rules_obj.search(self.env.cr, self.env.uid, [])
            for rule in rules_obj.browse(self.env.cr, self.env.uid, rules_id):
                if rule.shipping_method == 'consolidator':
                    self.shipping_rule = rule.id
                    break

            if not self.shipping_rule:
                raise osv.except_osv(_("Error"), _("Can not get auto shipping rule because no shipping rule for collector is defined."))

            # Get consolidator rule
            # check customer number
            if not self.partner_id.customer_number:
                raise osv.except_osv(_("Error"), _("Can not get auto collector rule because no customer number on this partner."))

            rules_obj = self.pool.get('stock.consolidator_rule')
            rules_id = rules_obj.search(self.env.cr, self.env.uid, [])
            for rule in rules_obj.browse(self.env.cr, self.env.uid, rules_id):
                if rule.customer_numbers and    self.partner_id.customer_number in rule.customer_numbers:
                    self.consolidator_rule = rule.id
                    break

            # label quantity
            self.logistic_unit_quantity = 1

            if not self.consolidator_rule:
                raise osv.except_osv(_("Error"), _("Can not get auto collector rule because customer number in any consolidator rule."))
            return

        # get shipping rules
        rules_obj = self.pool.get('stock.shipping_rule')
        rules = rules_obj.search(self.env.cr, self.env.uid, [], order='priority asc')

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
        if self.partner_id.country_id.id in countries_ruled:
            filter.append('|')
            filter.append(['country', '=', self.partner_id.country_id.id])
            filter.append(['country', '=', False])
        # check for europe
        else:
            if len(countries_ruled) > 0:
                regions_obj = self.pool.get('res.country.group')
                regions_id = regions_obj.search(self.env.cr, self.env.uid, [])
                region_match = False
                for region in regions_obj.browse(self.env.cr, self.env.uid, regions_id):
                    if self.partner_id.country_id in region.country_ids:
                        region_match = True
                        filter.append(['region', '=', region.id])
                # Measns that the country is in ROW
                if not region_match:
                    filter.append(['region', '=', 'ROW'])

        _logger.debug("Filter: %s", filter)

        rules = rules_obj.search(self.env.cr, self.env.uid, filter, order='priority asc')

        # loop on all rules to find the right one
        for rule in rules_obj.browse(self.env.cr, self.env.uid, rules):
            _logger.debug("Rule: %s - %s", rule.label_number, rule.service)
            # Shipping method (collector/standart/courrier)
            if rule.shipping_method == self.shipping_method:
                # Delivery method check between 'initial' and 'subsequent'
                if rule.delivery_method == 'both' or rule.delivery_method == self.file_id.job_id.settings_id.delivery_method or self.file_id.job_id.settings_id.delivery_method == 'both':

                    # PO-Box
                    if self.po_box == False or self.po_box == "" or self.po_box == "None":
                        if rule.po_box == "yes":
                            continue
                    elif self.po_box != False and self.po_box != "":
                        if rule.po_box == "no":
                            continue

                    # Postal-permit #
                    if self.postal_permit_number == False or self.postal_permit_number == "":
                        if rule.postal_permit == "yes":
                            continue
                    elif self.postal_permit_number != False and self.postal_permit_number != "":
                        if rule.postal_permit == "no":
                            continue

                    # ADS
                    if self.ads == False or self.ads == "":
                        if rule.ads == "yes":
                            continue
                    elif self.ads != False and self.ads != "":
                        if rule.ads == "no":
                            continue

                    # Phone
                    if self.partner_id.phone == "" or self.partner_id.phone == False:
                        if rule.phone == "yes":
                            continue
                    elif self.partner_id.phone != "" and self.partner_id.phone != False:
                        if rule.phone == "no":
                            continue

                    """
                    po_box_check = True
                    if rule.po_box == "yes" and (self.po_box == False or self.po_box == ""):
                        _logger.debug("POBOX")
                        po_box_check = False

                    postal_permit_check = True
                    if rule.postal_permit == "yes" and (self.postal_permit_number == False or self.postal_permit_number == ""):
                        _logger.debug("POPERMIT")
                        postal_permit_check = False


                    ads_check = True
                    if rule.ads == "yes" and (self.ads == False or self.ads == ""):
                        _logger.debug("ADS")
                        ads_check = False

                    # Phone
                    phone_check = True
                    if rule.phone == "yes" and (self.partner_id.phone == "" or self.partner_id.phone == False):
                        _logger.debug("PHONE")
                        phone_check = False

                    # check the checks
                    if not po_box_check or not postal_permit_check or not ads_check or not phone_check:
                        _logger.debug("CHECKS FAILED")
                        continue
                    """

                    # Weight
                    if rule.weight_max != 0 and self.net_picking_weight > rule.weight_max:
                        _logger.debug("Weight too much")
                        continue

                    if self.net_picking_weight < rule.weight_min:
                        _logger.debug("Weight too low")
                        continue

                    _logger.debug("Rule found: %s", rule.service)

                    # Number of packages
                    if rule.weight_max_package > 0 and rule.weight_max_package < self.net_picking_weight:
                        self.logistic_unit_quantity = int((self.net_picking_weight / rule.weight_max_package) + 1)
                    else:
                        self.logistic_unit_quantity = 1

                    #  Report
                    self.shipping_rule = rule
                    self.logistic_unit_report = rule.label_report
                    break

        # Create the boxes
        if len(self.boxes) < self.logistic_unit_quantity:
           i = 1
           while i <= self.logistic_unit_quantity:
                self.pool.get('stock.shipping_box').create(self.env.cr, self.env.uid, {
                    'picking_id': self.id,
                    'state': 'draft',
                })
                i += 1

        if not self.shipping_rule:
            raise osv.except_osv(_("Error"), _("There is no shipping rule that matches this picking list!"))


