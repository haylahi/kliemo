# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp.addons.document.document import nodefd_static
from thread import _local
from openerp import models, fields, api
from lxml import etree
from xml.dom import minidom
import openerp.tools as tools
from openerp.osv import osv
from openerp.tools.translate import _
import datetime
from zipfile import ZipFile
import os
import time
import logging
from openerp.osv import osv
_logger = logging.getLogger(__name__)


class MullerFile(models.Model):
    # -----------------------------------------------------------------------
    # MODEL INHERIT
    _inherit = ['kliemo_orders_parser.file']

    @api.multi
    def parse_again(self):
        """
        Will parse again an order file create the linked Picking list and POA file
        Will upload the generated POA file
        """
        if self.job_id.settings_id.type != 'muller':
            return super(MullerFile, self).parse_again()