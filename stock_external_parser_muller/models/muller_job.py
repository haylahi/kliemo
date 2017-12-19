from openerp import models, api
import openerp.tools as tools
from openerp.tools.translate import _
from openerp.osv import osv
import logging
import datetime

_logger = logging.getLogger(__name__)


class MullerJob(models.Model):
    _inherit = ['kliemo_orders_parser.job']

    @api.multi
    def run_job(self):
        # first, try to download and create files
        try:
            self.state = 'Running'

            cr = self.env.cr
            uid = self.env.user.id

            # get the files from the ftp
            in_file_ids = self.settings_id.download_files_and_save(self.id)

        except Exception, e:
            self.state = 'Cancelled'
            raise osv.except_osv(_("(job.runjob) Job failed (download) for %s") % self.settings_id.hostname,
                                 _("Here is the error:\n %s") % tools.ustr(e))

        # then for each file, try to parse
        try:
            # for each PO create a PL (which will create a POA)
            for file_id in in_file_ids:
                # TODO: make sure we are getting the parser from the  proper provider
                file_order = self.pool.get('kliemo_orders_parser.file').browse(cr, uid, file_id)
                file_order.createPickingList()

        except Exception, e:
            self.state = 'Cancelled'
            raise osv.except_osv(_("(job.runjob) Job failed (parsing) for %s") % self.settings_id.hostname,
                                 _("Here is the error:\n %s") % tools.ustr(e))
        # Check state of each file
        for my_file in self.files:
            if my_file.state == "Parsing Error":
                self.state = 'Error'
                return

        self.settings_id.last_execution_date = datetime.datetime.now()
        # Every file is OK
        self.state = 'Ended'
