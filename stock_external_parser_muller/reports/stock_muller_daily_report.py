# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import xlwt
from datetime import datetime
from openerp.osv import orm
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.tools.translate import translate, _
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'stock.muller.daily.report'

class stock_picking_list(orm.Model):
    _inherit = 'stock.picking'

    def _xls_muller_daily_pickings_report_fields(self, cr, uid, context=None):
        return [
            'external_order_number',
            'date',
            'product_quantity',
            'partner_id.muller_customer_number',
            'partner_id.name',
            'partner_id.street',
            'partner_id.street2',
            'partner_id.street3',
            'partner_id.city',
            'partner_id.zip',
            'partner_id.country_id.name',
            'partner_id.country_id.code',
            'delivery_type',
            'partner_id.login_app',
            'partner_id.letter_header',
        ]

    def _xls_all_pickings_template(self, cr, uid, context=None):
        """
        Template updates
        """
        return {}

class StockMullerDailyReportXLSParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(StockMullerDailyReportXLSParser, self).__init__(
            cr, uid, name, context=context)

        picking_obj = self.pool.get('stock.picking')
        self.context = context

        picking_fields = picking_obj._xls_muller_daily_pickings_report_fields(cr, uid, context)

        self.localcontext.update({
            'datetime': datetime,
            'picking_fields': picking_fields,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        res = translate(self.cr, _ir_translation_name, 'report', lang, src)
        return res or src


class StockMullerDailyReportXLS(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(StockMullerDailyReportXLS, self).__init__\
            (name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header

        # Report Column Headers format
        rh_cell_format = _xs['bold'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])

        # Type view Column format
        fill_blue = 'pattern: pattern solid, fore_color 27;'
        av_cell_format = _xs['bold'] + fill_blue + _xs['borders_all']
        self.av_cell_style = xlwt.easyxf(av_cell_format)
        self.av_cell_style_decimal = xlwt.easyxf(
            av_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # Type normal Column Data format
        an_cell_format = _xs['borders_all']
        self.an_cell_style = xlwt.easyxf(an_cell_format)
        self.an_cell_style_center = xlwt.easyxf(an_cell_format + _xs['center'])
        self.an_cell_style_date = xlwt.easyxf(
            an_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        self.an_cell_style_decimal = xlwt.easyxf(
            an_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(
            rt_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # XLS Template
        self.col_specs_template = {
            'external_order_number': {
                'header': [1, 20, 'text', _render("_('Beleglesezeile')")],
                'pickings': [1, 0, 'text', _render("pick.external_order_number")],
            },
            'date': {
                'header': [1, 40, 'text', _render("_('Datum')")],
                'pickings': [1, 0, 'text', _render("pick.date")],
            },
            'product_quantity': {
                'header': [1, 20, 'text', _render("_('Menge')")],
                'pickings': [1, 0, 'number', _render("pick.product_quantity")]
            },
            'partner_id.muller_customer_number': {
                'header': [1, 20, 'text', _render("_('Abonummer')")],
                'pickings': [1, 0, 'number', _render("pick.partner_id.muller_customer_number")]
            },
            'partner_id.name': {
                'header': [1, 20, 'text', _render("_('Customer')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.name"))]
            },
            'partner_id.street': {
                'header': [1, 20, 'text', _render("_('Street1')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.street"))]
            },
            'partner_id.street2': {
                'header': [1, 20, 'text', _render("_('Street2')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.street2"))]
            },
            'partner_id.street3': {
                'header': [1, 20, 'text', _render("_('Street3')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.street3"))]
            },
            'partner_id.city': {
                'header': [1, 20, 'text', _render("_('City')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.city"))]
            },
            'partner_id.zip': {
                'header': [1, 20, 'text', _render("_('Zip')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.zip"))]
            },
            'partner_id.country_id.name': {
                'header': [1, 20, 'text', _render("_('Country')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.country_id.name"))]
            },
            'partner_id.country_id.code': {
                'header': [1, 20, 'text', _render("_('Country Code')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.country_id.code"))]
            },
            'delivery_type': {
                'header': [1, 20, 'text', _render("_('Type')")],
                'pickings': [1, 0, 'text', _render(str("pick.delivery_type"))]
            },
             'partner_id.letter_header': {
                'header': [1, 20, 'text', _render("_('Briefanrede')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.letter_header"))]
            },
        }

    def _get_title(self):
        return "Muller Daily Report"

    def _get_pickings(self, ftp_settings_id, report_date, done_pickings):

        # Take all the picking for the selected date and related to the FTP setting
        condition = [['state', '!=', 'done'], ['state', '!=', 'cancel']]
        if done_pickings:
            condition = [['state', '=', 'done']]
        condition.append(['settings_id', '=', ftp_settings_id])
        #condition.append(('date_done', '<=', str(datetime.now().date()))) # TODO : filter on correct date
        _logger.debug("\n\nConditions : %s", condition)
        pickings_ids = picking_obj.search(cr, uid, condition)

        _logger.debug("Len: %s", len(pickings_ids))

        return pickings_ids
            

    def _view_add(self, acq, assets):
        parent = filter(lambda x: x[0] == acq[2], self.assets)
        if parent:
            parent = parent[0]
            if parent not in assets:
                self._view_add(parent, assets)
        assets.append(acq)

    def _all_pickings_report(self, _p, _xs, data, objects, wb):
        cr = self.cr
        uid = self.uid
        context = self.context
        picking_fields = _p.picking_fields

        title = self._get_title()
        title_short = self._get_title()
        ws = wb.add_sheet("Muller-Daily-Report")

        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Set header
        c_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}),  picking_fields)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row( ws, row_pos, row_data, row_style=self.rh_cell_style_center, set_column_size=False)

        services = []

        for pick in self.pickings:
            if pick.shipping_rule.id not in services:
                services.append(pick.shipping_rule.id)
            c_specs = map(lambda x: self.render(x, self.col_specs_template, 'pickings'), picking_fields)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row( ws, row_pos, row_data, row_style=self.an_cell_style )


        # Create a page for each service
        for serv in services:
            srow_pos = 0
            shipping_rule = self.pool.get('stock.shipping_rule').browse(cr, uid, serv)
            _logger.debug("\nservice: %s", shipping_rule.service)

            if shipping_rule.service:
                # New sheet
                ws = wb.add_sheet(shipping_rule.service)
                # Set header
                sc_specs = map(lambda x: self.render(x, self.col_specs_template, 'header', render_space={'_': _p._}),  picking_fields)
                srow_data = self.xls_row_template(sc_specs, [x[0] for x in sc_specs])
                srow_pos = self.xls_write_row( ws, srow_pos, srow_data, row_style=self.rh_cell_style_center, set_column_size=False)

                for pick in self.pickings:
                    if pick.shipping_rule.id == serv:
                        sc_specs = map(lambda x: self.render(x, self.col_specs_template, 'pickings'), picking_fields)
                        srow_data = self.xls_row_template(sc_specs, [x[0] for x in sc_specs])
                        srow_pos = self.xls_write_row( ws, srow_pos, srow_data, row_style=self.an_cell_style )

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        picking_fields = _p.picking_fields
        ftp_setting_id = data['ftp_setting']
        report_date = data['report_date']
        done_pickings = data['done_pickings']

        _ = _p._

        report_name = self._get_title()

        _logger.debug("\n\nPickings : %s", data['ids'])

        self.pickings = self._get_pickings(ftp_setting_id, report_date, done_pickings)
        self.pickings_id = [x.id for x in self.pickings]
        self._all_pickings_report(_p, _xs, data, objects, wb)

StockMullerDailyReportXLS(
    'report.stock.muller.daily.xls',
    'stock.picking',
    parser=StockMullerDailyReportXLSParser)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: