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

class wiz_presse_und_buch_reports(osv.osv_memory):

    _name = 'wiz.stock.presse_und_buch.daily.report'
    _description = 'Stock P&B + Airmail Report'

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
                    pickings.append(picking)

                    #if picking.shipping_rule.code == "PB" or picking.shipping_rule.code == "DL":
                        

        _logger.debug("Len: %s", len(pickings))

        result_dict = {
            'priority_eu_nb': 0,
            'priority_eu_weight': 0,
            'economy_eu_nb' : 0,
            'economy_eu_weight' : 0,
            'priority_non_eu_nb' : 0,
            'priority_non_eu_weight' : 0,
            'economy_non_eu_nb' : 0,
            'economy_non_eu_weight' : 0,
            'total_nb' : 0,
            'total_weight' : 0,
        }

        # get the weight
        for picking in pickings:
            # Priority EU
            # Not used

            # Economy EU
            if picking.shipping_rule.code == "PB":
                result_dict['economy_eu_nb'] = result_dict['economy_eu_nb']  + 1
                result_dict['economy_eu_weight'] = result_dict['economy_eu_weight'] + picking.net_picking_weight
                 # Total
                result_dict['total_nb'] = result_dict['total_nb'] + 1
                result_dict['total_weight'] = result_dict['total_weight'] + picking.net_picking_weight
                continue

            # Priority Non-EU
            if picking.shipping_rule.code == "DL":
                result_dict['priority_non_eu_nb'] = result_dict['priority_non_eu_nb']  + 1
                result_dict['priority_non_eu_weight'] = result_dict['priority_non_eu_weight'] + picking.net_picking_weight
                 # Total
                result_dict['total_nb'] = result_dict['total_nb'] + 1
                result_dict['total_weight'] = result_dict['total_weight'] + picking.net_picking_weight
                continue

            # Economy Non-EU (typically Switzerland)
            if picking.shipping_rule.code == "CH":
                result_dict['economy_non_eu_nb'] = result_dict['economy_non_eu_nb']  + 1
                result_dict['economy_non_eu_weight'] = result_dict['economy_non_eu_weight'] + picking.net_picking_weight
                 # Total
                result_dict['total_nb'] = result_dict['total_nb'] + 1
                result_dict['total_weight'] = result_dict['total_weight'] + picking.net_picking_weight
                continue

        return result_dict

    def get_report(self, cr, uid, ids, context=None):
        data = self._get_datas(cr, uid, ids, context=context)

        datas = {
            'ids': [],
            'model': 'wiz.stock.presse_und_buch.daily.report',
            'form': data,
        }
        return self.pool['report'].get_action(cr, uid, [], 'stock_presse_und_buch_report.stock_presse_und_buch_report_document', data=datas, context=context)

class wiz_presse_und_buch_reports_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(wiz_presse_und_buch_reports_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })

class wrapped_wiz_presse_und_buch_reports_print(osv.AbstractModel):
    _name = 'report.stock_presse_und_buch_report.stock_presse_und_buch_report_document'
    _inherit = 'report.abstract_report'
    _template = 'stock_presse_und_buch_report.stock_presse_und_buch_report_document'
    _wrapped_report_class = wiz_presse_und_buch_reports_print
        

