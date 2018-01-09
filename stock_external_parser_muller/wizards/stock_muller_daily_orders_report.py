# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp.osv import orm, fields
from openerp.tools.translate import _
import time
import datetime

import logging
_logger = logging.getLogger(__name__)

class WizardStockMullerDailyReport(orm.TransientModel):

    _name = 'wiz.stock.muller.daily.report'
    _description = 'Stock Muller Daily Report'

    _columns = {
        'report_date' : fields.date(
          'Report date', required=True
        ),
        'ftp_setting' : fields.many2one(
            'kliemo_orders_parser.ftpsettings',
            'FTP connector',
        ),
        'done_pickings' : fields.boolean(
          'Only done pickings', default=True,
        ),
    }
    _defaults= {
        'report_date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def xls_export(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        wiz_form = self.browse(cr, uid, ids)[0]
        report_date = wiz_form.report_date
        ftp_setting = wiz_form.ftp_setting.id
        done_pickings = wiz_form.done_pickings

        # Take all the picking for the selected date and related to the FTP setting
        pickings = []
        condition = [['state', '!=', 'done'], ['state', '!=', 'cancel']]
        if done_pickings:
            condition = [['state', '=', 'done']]
        pickings_ids = picking_obj.search(cr, uid, condition)
        for pick_id in pickings_ids:
            picking = picking_obj.browse(cr, uid, pick_id)

            # Only done pickings so check the date
            if done_pickings:
                date = datetime.datetime.strptime(picking.date_done, "%Y-%m-%d %H:%M:%S")
                date = datetime.datetime.strftime(date, "%Y-%m-%d")
                if date == report_date:
                    # Take all corresponding to the ftp_setting OR all (no mather which ftp setting)
                    if (ftp_setting == False) or (ftp_setting != False and picking.file_id.job_id.settings_id.id == ftp_setting):
                        pickings.append(picking.id)
            # Every not done pickings
            else:
                if (ftp_setting == False) or (ftp_setting != False and picking.file_id.job_id.settings_id.id == ftp_setting):
                        pickings.append(picking.id)

        _logger.debug("Len: %s", len(pickings))

        if len(pickings) < 1:
            raise orm.except_orm(
                _('No Data Available'),
                _('No records found for your selection!'))

        report = {
            'type': 'ir.actions.report.xml',
            'report_name': 'stock.muller.daily.xls',
            'datas': {
                'model': 'stock.picking',
                'report_date': report_date,
                'ftp_setting': ftp_setting,
                'done_pickings': done_pickings,
                'ids': pickings,
            }
        }
        return report
