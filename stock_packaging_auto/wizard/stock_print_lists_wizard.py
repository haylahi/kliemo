# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp.osv import orm, fields
import time
import datetime
from openerp.osv import osv
from openerp import _

import logging
_logger = logging.getLogger(__name__)

class wiz_print_picking_lists(orm.TransientModel):

    _name = 'wiz.stock.picking.print.lists'
    _description = 'Print Stock Pickings'

    _columns = {
        'report_date' : fields.date(
          'Report date', required=True
        ),
        'state' : fields.selection((
            ['all', 'All'],
            ['draft', 'Draft'],
            ['cancel', 'Cancelled'],
            ['waiting', 'Waiting'],
            ['confirmed', 'Waiting Availability'],
            ['partially_available', 'Partially Available'],
            ['assigned', 'Ready'],
            ['done', 'Transferred']),
            'State',
        ),
    }
    _defaults= {
        'report_date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': 'assigned',
    }

    def print_pickings(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        wiz_form = self.browse(cr, uid, ids)[0]
        report_date = wiz_form.report_date
        state = wiz_form.state
        fil = []
        if state != 'all':
            fil.append(['state', '=', state])

        # Take all the picking for the selected date and related to the FTP setting
        pickings = []
        pickings_ids = picking_obj.search(cr, uid, fil)
        for pick_id in pickings_ids:
            picking = picking_obj.browse(cr, uid, pick_id)
            date = datetime.datetime.strptime(picking.date, "%Y-%m-%d %H:%M:%S")
            date = datetime.datetime.strftime(date, "%Y-%m-%d")
            if date == report_date:
                pickings.append(picking.id)

        if len(pickings) < 1:
            raise osv.except_osv(_("Error"), _("No picking list for the specified state and date."))

        return self.pool['report'].get_action(cr, uid, pickings, 'stock.report_picking', context=context)
