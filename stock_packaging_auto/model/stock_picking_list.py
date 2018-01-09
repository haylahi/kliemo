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

        elif self.settings_type == "muller":
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
     # Used as an Interface
    @api.multi
    def compute_shipping(self):
        return True


