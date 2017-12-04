# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class product_magazine(models.Model):
    _inherit = ['product.template']

    is_magazine = fields.Boolean(string="Magazine")

    # Fields added to manage magazines
    periodicity = fields.Selection([('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('semester', 'Semester'), ('year', 'Year')], string="Periodicity")
    period = fields.Integer(string="Period")
    journal_id = fields.Char(string="Journal ID")
    wbs_element = fields.Char(string="WBS-element")
    periodical_permit_number = fields.Char(string="Periodical Permit Number")
    dimension_width = fields.Integer(string="Width", default="210")
    dimension_height = fields.Integer(string="Height", default="279")
    issn_print = fields.Char(string="ISSN (Print)")
    issn_online = fields.Char(string="ISSN (Online)")
    default_code = fields.Char(compute="_compute_reference_for_issues", string="Internal reference & barcode")

    @api.one
    @api.onchange('journal_id')
    def _compute_reference_for_issues(self):
        if self.is_magazine:
            self.default_code = self.journal_id
            for issue in self.product_variant_ids:
                if issue.issue_volume and issue.issue_number:
                    issue.default_code = self.journal_id + "-" + issue.issue_volume + "-" + issue.issue_number

    @api.multi
    def print_labels(self):
        if len(self.product_variant_ids) < 1:
            raise osv.except_osv(_("There is no issue!"), _("Impossible to print issues while there is none define"))
        table = []
        for issue in self.product_variant_ids:
            table.append(issue.id)
        return self.pool['report'].get_action(self.env.cr, self.env.uid, table, 'product_magazine.issue_label', context=self.env.context)

    @api.multi
    def print_labels_with_stock_location(self):
        if len(self.product_variant_ids) < 1:
            raise osv.except_osv(_("There is no issue!"), _("Impossible to print issues while there is none define"))
        print_ids = []
        for issue in self.product_variant_ids:
            stock_quants_obj = self.pool.get('stock.quant')
            stock_quants_ids = stock_quants_obj.search(self.env.cr, self.env.uid, [('product_id', '=', issue.id)])
            if len(stock_quants_ids) > 0:
                for i in stock_quants_ids:
                    print_ids.append(i)
        if len(print_ids) < 1:
            raise osv.except_osv(_("No Issue in stock."), _("Impossible to print the stock location for this magazines because there is not issue on stock. Use the other button for simple labels"))

        return self.pool['report'].get_action(self.env.cr, self.env.uid, print_ids, 'product_magazine.issue_label_stock', context=self.env.context)