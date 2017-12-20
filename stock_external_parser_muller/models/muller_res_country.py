# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp import models, fields, api
import logging
from openerp.osv import osv

class MullerResCountry(models.Model):
    # parent generic parser
    _inherit = ['res.country']

    muller_country_code = fields.Char(string="Muller Country Code")