# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp import models, fields, api
import logging
from openerp.osv import osv

class MullerResPartner(models.Model):
    _inherit = ['res.partner']

    muller_customer_number = fields.Char(string="Customer Number (Muller)")
    letter_header = fields.Char(string="Letter header")
    login_app = fields.Char(string="Login APP")
    subscription_ids = fields.One2many('muller.subscription', 'partner_id', string="Subscriptions")
    