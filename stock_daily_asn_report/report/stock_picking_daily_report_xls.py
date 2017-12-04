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

_ir_translation_name = 'stock.picking.asn.report'

class stock_picking_asn_report_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(stock_picking_asn_report_xls_parser, self).__init__(
            cr, uid, name, context=context)

        picking_obj = self.pool.get('stock.picking')
        self.context = context

        picking_fields = picking_obj._xls_all_pickings_report_fields(cr, uid, context)

        self.localcontext.update({
            'datetime': datetime,
            'picking_fields': picking_fields,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        res = translate(self.cr, _ir_translation_name, 'report', lang, src)
        return res or src


class stock_picking_asn_report_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(stock_picking_asn_report_xls, self).__init__\
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
                'header': [1, 20, 'text', _render("_('PO#')")],
                'pickings': [1, 0, 'text', _render("pick.external_order_number")],
            },
            'date': {
                'header': [1, 40, 'text', _render("_('Order Date')")],
                'pickings': [1, 0, 'text', _render("pick.date")],
            },
            'asn_date': {
                'header': [1, 20, 'text', _render("_('ASN Date')")],
               'pickings': [1, 0, 'text', _render("pick.asn_date")],
            },
            'tat': {
                'header': [1, 20, 'text', _render("_('TAT')")],
                'pickings': [1, 0, 'text', _render(str("pick.tat"))]
            },
            'product_quantity': {
                'header': [1, 20, 'text', _render("_('#Copies')")],
                'pickings': [1, 0, 'number', _render("pick.product_quantity")]
            },
            'net_picking_weight': {
                'header': [1, 20, 'text', _render("_('Net Weight')")],
                'pickings': [1, 0, 'number', _render("pick.net_picking_weight")]
            },
            'total_picking_weight': {
                'header': [1, 20, 'text', _render("_('Gross Weight')")],
                'pickings': [1, 0, 'number', _render("pick.total_picking_weight")]
            },
            'logistic_unit_quantity': {
                'header': [1, 20, 'text', _render("_('# Boxes')")],
                'pickings': [1, 0, 'number', _render("pick.logistic_unit_quantity")]
            },
            'shipping_rule.code': {
                'header': [1, 20, 'text', _render("_('')")],
                'pickings': [1, 0, 'text', _render("pick.shipping_rule.code")]
            },
            'shipping_rule.label_number': {
                'header': [1, 20, 'text', _render("_('')")],
                'pickings': [1, 0, 'number', _render("pick.shipping_rule.label_number")]
            },
            'shipping_rule.service': {
                'header': [1, 20, 'text', _render("_('Shipping')")],
                'pickings': [1, 0, 'text', _render(str("pick.shipping_rule.service"))]
            },
            'tracking_number': {
                 'header': [1, 20, 'text', _render("_('Tracking numbers')")],
                 'pickings': [1, 0, 'text', _render("pick.tracking_number")]
            },
            'partner_id.country_id.code': {
                'header': [1, 20, 'text', _render("_('County')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.country_id.code"))]
            },
            'partner_id.customer_number': {
                'header': [1, 20, 'text', _render("_('Customer#')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.customer_number"))]
            },
            'partner_id.name': {
                'header': [1, 20, 'text', _render("_('Address')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.name"))]
            },
            'partner_id.street': {
                'header': [1, 20, 'text', _render("_('Address2')")],
                'pickings': [1, 0, 'text', _render(str("pick.partner_id.street"))]
            },
        }

    def _get_title(self):
        return "TITLE"

    def _report_title(self, ws, _p, row_pos, _xs, title):
        cell_style = xlwt.easyxf(_xs['xls_title'])
        c_specs = [
            ('report_name', 1, 0, 'text', title),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)
        return row_pos + 1

    def _empty_report(self, ws, _p, row_pos, _xs, report):
        cell_style = xlwt.easyxf(_xs['bold'])

        if report == 'acquisition':
            suffix = _('New Acquisitions')
        elif report == 'active':
            suffix = _('Active Assets')
        else:
            suffix = _('Removed Assets')
        no_entries = _("No") + " " + suffix
        c_specs = [
            ('ne', 1, 0, 'text', no_entries),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)

    def _get_pickings(self, ftp_settings_id, report_date, done_pickings):

        pickings = []
        picking_obj = self.pool.get('stock.picking')
        condition = [['state', '!=', 'done'], ['state', '!=', 'cancel']]
        if done_pickings:
            condition = [['state', '=', 'done']]
        pickings_ids = picking_obj.search(self.cr, self.uid, condition)
        for pick_id in pickings_ids:
            picking = picking_obj.browse(self.cr, self.uid, pick_id)

            # Only done pickings so check the date
            if done_pickings:
                date = datetime.strptime(picking.date_done, "%Y-%m-%d %H:%M:%S")
                date = datetime.strftime(date, "%Y-%m-%d")
                if date == report_date:
                    # Take all corresponding to the ftp_setting OR all (no mather which ftp setting)
                    if (ftp_settings_id == False) or (ftp_settings_id != False and picking.file_id.job_id.settings_id.id == ftp_settings_id):
                        pickings.append(picking)
            # Every not done pickings
            else:
                if (ftp_settings_id == False) or (ftp_settings_id != False and picking.file_id and picking.file_id.job_id and picking.file_id.job_id.settings_id and picking.file_id.job_id.settings_id.id == ftp_settings_id):
                        pickings.append(picking)

        _logger.debug("Len: %s", len(pickings))

        return pickings

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
        ws = wb.add_sheet("ASN-Report")

        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']
        #row_pos = self._report_title(ws, _p, row_pos, _xs, title) # Removed to not show a title

        if not self.pickings:
            return self._empty_report(ws, _p, row_pos, _xs, 'active')

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

        self.pickings = self._get_pickings(ftp_setting_id, report_date, done_pickings)
        self.pickings_id = [x.id for x in self.pickings]
        self._all_pickings_report(_p, _xs, data, objects, wb)

stock_picking_asn_report_xls(
    'report.stock.picking.asn.xls',
    'stock.picking',
    parser=stock_picking_asn_report_xls_parser)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
