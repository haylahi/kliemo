# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp import models, api, fields
import logging


_logger = logging.getLogger(__name__)


class MullerSubscription(models.Model):
    _name = 'muller.subscription'

    partner_id = fields.Many2one('res.partner', string="Partner", required=True, delete="cascade")
    number = fields.Char(string="Number", required=True)
