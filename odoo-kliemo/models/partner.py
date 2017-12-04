# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models, fields

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = ['res.partner']

    street3 = fields.Char(string="Street3")
    customer_number = fields.Char(string="Customer Number")
    endorsement_line_1 = fields.Char(string="Endorsement line 1")
    endorsement_line_2 = fields.Char(string="Endorsement line 2")
    