# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class SpringerMagazine(models.Model):
    _inherit = ['product.template']

    wbs_element = fields.Char(string="WBS-element")
    periodical_permit_number = fields.Char(string="Periodical Permit Number")

