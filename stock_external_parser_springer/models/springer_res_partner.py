# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp import models, fields, api
import logging
from openerp.osv import osv

class SpringerResPartner(models.Model):
    _inherit = ['res.partner']

    customer_number = fields.Char(string="Customer Number (Springer)")
    endorsement_line_1 = fields.Char(string="Endorsement line 1")
    endorsement_line_2 = fields.Char(string="Endorsement line 2")