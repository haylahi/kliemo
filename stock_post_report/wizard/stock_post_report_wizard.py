# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.report import report_sxw
import time
import datetime

import logging
_logger = logging.getLogger(__name__)

class wiz_post_reports(osv.osv_memory):

    _name = 'wiz.stock.post.daily.report'
    _description = 'Stock POST Report'

    _columns = {
        'report_date' : fields.date(
          'Report date', required=True
        ),
        'ftp_setting' : fields.many2one(
            'kliemo_orders_parser.ftpsettings',
            'FTP connector',
        ),
    }
    _defaults= {
        'report_date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def _get_datas(self, cr, uid, ids, context=None):
        wiz_data = self.browse(cr, uid, ids[0], context=context)

        picking_obj = self.pool.get('stock.picking')
        wiz_form = self.browse(cr, uid, ids)[0]
        report_date = wiz_form.report_date
        ftp_setting = wiz_form.ftp_setting.id

        # Take all the picking for the selected date and related to the FTP setting
        pickings = []
        pickings_ids = picking_obj.search(cr, uid, [['state', '=', 'done']])
        for pick_id in pickings_ids:
            picking = picking_obj.browse(cr, uid, pick_id)
            date = datetime.datetime.strptime(picking.date_done, "%Y-%m-%d %H:%M:%S")
            date = datetime.datetime.strftime(date, "%Y-%m-%d")
            if date == report_date:
                # Take all corresponding to the ftp_setting OR all (no mather which ftp setting)
                if (ftp_setting == False) or (ftp_setting != False and picking.file_id.job_id.settings_id.id == ftp_setting):
                    if picking.shipping_rule.code == "SB":
                        pickings.append(picking)

        _logger.debug("Len: %s", len(pickings))

        result_dict = {
            '_50g_num': 0,
            '51g_100g_num': 0,
            '101g_250g_num': 0,
            '251g_500g_num': 0,
            '501g_1000g_num': 0,
            '_50g_weight': 0,
            '51g_100g_weight': 0,
            '101g_250g_weight': 0,
            '251g_500g_weight': 0,
            '501g_1000g_weight': 0,
            '_50g_price': 0.55,
            '51g_100g_price': 0.8,
            '101g_250g_price': 0.95,
            '251g_500g_price': 1.3,
            '501g_1000g_price': 1.8,
            '_50g_total': 0,
            '51g_100g_total': 0,
            '101g_250g_total': 0,
            '251g_500g_total': 0,
            '501g_1000g_total': 0,
            'total_num': len(pickings),
            'total_weight': 0,
            'total_price': 0,
        }

        # get the weights
        for pick in pickings:
            if pick.net_picking_weight <= 0.05:
                result_dict['_50g_num'] = result_dict['_50g_num'] + 1
                result_dict['_50g_weight'] = result_dict['_50g_weight'] + pick.net_picking_weight
                result_dict['_50g_total'] = result_dict['_50g_num'] *  result_dict['_50g_price']
                continue
            if pick.net_picking_weight <= 0.1:
                result_dict['51g_100g_num'] = result_dict['51g_100g_num'] + 1
                result_dict['51g_100g_weight'] = result_dict['51g_100g_weight'] + pick.net_picking_weight
                result_dict['51g_100g_total'] = result_dict['51g_100g_num'] *  result_dict['51g_100g_price']
                continue
            if pick.net_picking_weight <= 0.25:
                result_dict['101g_250g_num'] = result_dict['101g_250g_num'] + 1
                result_dict['101g_250g_weight'] = result_dict['101g_250g_weight'] + pick.net_picking_weight
                result_dict['101g_250g_total'] = result_dict['101g_250g_num'] *  result_dict['101g_250g_price']
                continue
            if pick.net_picking_weight <= 0.5:
                result_dict['251g_500g_num'] = result_dict['251g_500g_num'] + 1
                result_dict['251g_500g_weight'] = result_dict['251g_500g_weight'] + pick.net_picking_weight
                result_dict['251g_500g_total'] = result_dict['251g_500g_num'] *  result_dict['251g_500g_price']
                continue
            if pick.net_picking_weight <= 1:
                result_dict['501g_1000g_num'] = result_dict['501g_1000g_num'] + 1
                result_dict['501g_1000g_weight'] = result_dict['501g_1000g_weight'] + pick.net_picking_weight
                result_dict['501g_1000g_total'] = result_dict['501g_1000g_num'] *  result_dict['501g_1000g_price']
                continue

        result_dict['total_weight'] = result_dict['_50g_weight'] + result_dict['51g_100g_weight'] + result_dict['101g_250g_weight'] + result_dict['251g_500g_weight'] + result_dict['501g_1000g_weight']
        result_dict['total_price'] = result_dict['_50g_total'] + result_dict['51g_100g_total'] + result_dict['101g_250g_total'] + result_dict['251g_500g_total'] + result_dict['501g_1000g_total']

        return result_dict

    def get_report(self, cr, uid, ids, context=None):
        data = self._get_datas(cr, uid, ids, context=context)

        datas = {
            'ids': [],
            'model': 'wiz.stock.post.daily.report',
            'form': data,
        }
        return self.pool['report'].get_action(cr, uid, [], 'stock_post_report.stock_post_report_document', data=datas, context=context)

class wiz_post_reports_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(wiz_post_reports_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })

class wrapped_wiz_post_reports_print(osv.AbstractModel):
    _name = 'report.stock_post_report.stock_post_report_document'
    _inherit = 'report.abstract_report'
    _template = 'stock_post_report.stock_post_report_document'
    _wrapped_report_class = wiz_post_reports_print
        

