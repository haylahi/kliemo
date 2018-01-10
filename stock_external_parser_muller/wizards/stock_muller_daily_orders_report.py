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
            required=True,
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

        

        """if len(pickings_ids) < 1:
            raise orm.except_orm(
                _('No Data Available'),
                _('No records found for your selection!'))
        """

        report = {
            'type': 'ir.actions.report.xml',
            'report_name': 'stock.muller.daily.xls',
            'datas': {
                'model': 'stock.picking',
                'report_date': report_date,
                'ftp_setting': ftp_setting,
                'done_pickings': done_pickings,
                'ids': pickings_ids,
            }
        }
        return report
