# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models, fields, api
_logger = logging.getLogger(__name__)

class MullerShippingRule(models.Model):
    _inherit = ['stock.shipping_rule']

    used_for_muller = fields.Boolean(string="Used for Müller", default=False)
    max_issues_per_shipping = fields.Integer(string="Maximum number of issue per shipping")
