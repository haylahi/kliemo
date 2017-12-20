from openerp import models, api
import openerp.tools as tools
from openerp.osv import osv
import logging
import datetime

_logger = logging.getLogger(__name__)


class SpringerJob(models.Model):
    _inherit = ['kliemo_orders_parser.job']

    @api.multi
    def run_job(self):
        if self.settings_id.type != 'springer':
            return super(SpringerJob, self).run_job()

        # first, try to download and create files
        try:
            self.state = 'Running'

            cr = self.env.cr
            uid = self.env.user.id

            poa_file_ids = []

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
                file_order = self.pool.get('kliemo_orders_parser.file').browse(cr, uid, file_id)
                file_poaid = file_order.createPickingList()
                poa_file_ids.append(file_poaid)

        except Exception, e:
            self.state = 'Cancelled'
            raise osv.except_osv(_("(job.runjob) Job failed (parsing) for %s") % self.settings_id.hostname,
                                 _("Here is the error:\n %s") % tools.ustr(e))

        # finally upload POAs
        try:
            # for each POA, upload them
            if len(poa_file_ids) > 0:
                self.settings_id.upload_files(poa_file_ids, File.TYPEPOA)

        except Exception, e:
            self.state = 'Cancelled'
            raise osv.except_osv(_("(job.runjob) Job failed (uploading POAs) for %s") % self.settings_id.hostname,
                                 _("Here is the error:\n %s") % tools.ustr(e))

            # Check state of each file
        for my_file in self.files:
            if my_file.state == "Parsing Error":
                self.state = 'Error'
                return
            # Remove the my_file removal because of problems
            # else:
            #    os.remove('/tmp/' + file.name)

        self.settings_id.last_execution_date = datetime.datetime.now()
        # Every file is OK
        self.state = 'Ended'