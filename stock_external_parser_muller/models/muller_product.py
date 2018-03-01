# This code has been written
# by AbAKUS it-solutions PGmbH

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class MullerMagazine(models.Model):
    _inherit = ['product.template']

    used_for_muller = fields.Boolean(string="Used for Muller", default=False)

