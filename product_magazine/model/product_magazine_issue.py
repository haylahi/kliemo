# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class product_magazine(models.Model):
    _inherit = ['product.product']

    # Fields added to manage issues
    title = fields.Char(string="Title")
    # ean not made cause already existing
    issue_number = fields.Char(string="Issue #")
    issue_volume = fields.Char(string="Issue volume")
    issue_date = fields.Date(string="Issue date")
    issue_type = fields.Selection([('regular', 'Regular'), ('special', 'Special')], string="Issue type", default='regular')
    default_code = fields.Char(compute="_compute_reference", string="Internal reference & barcode")

    @api.one
    @api.depends('issue_number', 'issue_volume')
    def _compute_reference(self):
        if self.product_tmpl_id.is_magazine:
            if self.issue_volume and self.issue_number:
                if self.issue_type == 'special':
                    self.default_code = self.product_tmpl_id.journal_id + "-" + self.issue_volume + "-S" + self.issue_number
                else:
                    self.default_code = self.product_tmpl_id.journal_id + "-" + self.issue_volume + "-" + self.issue_number

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.issue_type == 'special':
                result.append((record.id, "%s | %s - %s | SUPPLEMENT | %s" % (record.product_tmpl_id.journal_id, record.issue_volume, record.issue_number, record.product_tmpl_id.name)))
            else:
                result.append((record.id, "%s | %s - %s | %s" % (record.product_tmpl_id.journal_id, record.issue_volume, record.issue_number, record.product_tmpl_id.name)))
        return result

    def print_label(self, cr, uid, ids, context=None):
        return self.pool['report'].get_action(cr, uid, ids, 'product_magazine.issue_label', context=context)

    def print_label_with_stock_location(self, cr, uid, ids, context=None):
        print_ids = []
        for issue_id in ids:
            stock_quants_obj = self.pool.get('stock.quant')
            stock_quants_ids = stock_quants_obj.search(cr, uid, [('product_id', '=', issue_id)])
            for i in stock_quants_ids:
                print_ids.append(i)
        if len(print_ids) < 1:
            raise osv.except_osv(_("No Issue in stock."), _("Impossible to print the stock location for this magazines because there is not issue on stock. Use the other button for simple labels"))

        return self.pool['report'].get_action(cr, uid, print_ids, 'product_magazine.issue_label_stock', context=context)
