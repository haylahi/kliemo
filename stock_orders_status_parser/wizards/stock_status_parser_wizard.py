# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api


import logging
_logger = logging.getLogger(__name__)

class wizard_warehouse_orders_status(models.TransientModel):

    _name = 'wizard.warehouse.orders.status'

    text = fields.Text('Orders (one per line)', required=True)

    @api.multi
    def get_orders_status(self):
        self.ensure_one()
        lines = self.text.split('\n')
        new_text = "order number, kliemo number, state, asn, asn date\n"

        for line in lines:
            if line == "":
                continue
            # line is the order nymber, get info
            picking = self.env['stock.picking'].search([('external_order_number', 'like', str(line))])
            _logger.debug("%s", picking)
            if len(picking) < 1:
                new_text += line + ", NOT IN THE SYSTEM, /, /, /\n"
                continue
            if len(picking) == 1:
                # original number
                new_text += line
                # odoo number
                new_text += ", " + picking.name
                # state
                if picking.state == 'done':
                    new_text += ", transfered"
                else:
                     new_text += ", " + picking.state
                if picking.asn_file_id:
                    new_text += ", Yes"
                    new_text += ", " + picking.asn_date
                else:
                    new_text += ", No, "
                new_text += "\n"

            
        self.text = new_text

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.warehouse.orders.status',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            }
            
