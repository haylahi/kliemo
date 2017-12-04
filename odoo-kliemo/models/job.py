# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
import openerp.tools as tools
import zipfile
import os
import shutil
import datetime
import StringIO
from file import File
import time

import logging
_logger = logging.getLogger(__name__)

class job(models.Model):
    # -----------------------------------------------------------------------
    # MODEL NAME
    _name = 'kliemo_orders_parser.job'

    # -----------------------------------------------------------------------
    # STATES DICTIONARY
    STATUS_WAITING = "Waiting"
    STATUS_RUNNING = "Running"
    STATUS_ENDED = "Ended"
    STATUS_CANCELLED = "Cancelled"
    STATUS_ERROR = "Error"

    # -----------------------------------------------------------------------
    # MODEL FIELDS
    date = fields.Datetime(String="Date", required=True)
    settings_id = fields.Many2one('kliemo_orders_parser.ftpsettings', ondelete='cascade', string="Settings", required=True)
    state = fields.Selection([(STATUS_WAITING, STATUS_WAITING), (STATUS_RUNNING, STATUS_RUNNING), (STATUS_ENDED, STATUS_ENDED), (STATUS_CANCELLED, STATUS_CANCELLED), (STATUS_ERROR, STATUS_ERROR)], default=STATUS_WAITING)
    files = fields.One2many('kliemo_orders_parser.file', 'job_id', string="Files")

    # -----------------------------------------------------------------------
    # METHOD ACTIONS TRIGERRED BY BUTTONS
    @api.multi
    def action_set_as_error(self):
        self.setAsError()

    @api.multi
    def action_unset_as_error(self):
        self.setAsErrorFixed()

    @api.multi
    def action_run_job(self):
        self.run_job()

    @api.multi
    def action_cancel_job(self):
        self.cancel_job()

    @api.multi
    def action_draft_job(self):
        self.draft_job()

    # -----------------------------------------------------------------------
    # ODOO INHERIT METHODS
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s - %s" % (record.settings_id.name, record.date)))
        return result

    # -----------------------------------------------------------------------
    # MODEL METHODS
    @api.multi
    def setAsError(self):
        self.state = job.STATUS_ERROR

    @api.multi
    def setAsErrorFixed(self):
        all_ok = True
        for file in self.files:
            if file.state == 'Parsing Error':
                self.state = job.STATUS_ERROR
                return
            if file.state == 'Running':
                all_ok = False
        if not all_ok:
            self.state = job.STATUS_RUNNING
        else:
            self.state = job.STATUS_ENDED

    @api.multi
    def cancel_job(self):
        self.state = job.STATUS_CANCELLED

    @api.multi
    def draft_job(self):
        self.state = job.STATUS_WAITING

    @api.multi
    def run_job(self):
        # first, try to download and create files
        try:
            self.state = job.STATUS_RUNNING

            cr = self.env.cr
            uid = self.env.user.id

            poa_file_ids = []

            # get the files from the ftp
            in_file_ids = self.settings_id.download_files_and_save(self.id)

        except Exception, e:
            self.state = job.STATUS_CANCELLED
            raise osv.except_osv(_("(job.runjob) Job failed (download) for %s") % self.settings_id.hostname, _("Here is the error:\n %s") % tools.ustr(e))

        # then for each file, try to parse
        try:
            # for each PO create a PL (which will create a POA)
            for file_id in in_file_ids:
                fileorder = self.pool.get('kliemo_orders_parser.file').browse(cr, uid, file_id)
                filepoaid = fileorder.createPickingList()
                poa_file_ids.append(filepoaid)

        except Exception, e:
            self.state = job.STATUS_CANCELLED
            raise osv.except_osv(_("(job.runjob) Job failed (parsing) for %s") % self.settings_id.hostname, _("Here is the error:\n %s") % tools.ustr(e))

        # finally upload POAs   
        try:
            # for each POA, upload them
            if len(poa_file_ids) > 0:
                self.settings_id.upload_files(poa_file_ids, File.TYPEPOA)

        except Exception, e:
            self.state = job.STATUS_CANCELLED
            raise osv.except_osv(_("(job.runjob) Job failed (uploading POAs) for %s") % self.settings_id.hostname, _("Here is the error:\n %s") % tools.ustr(e))   
        
        # Check state of each file
        for file in self.files:
            if file.state == "Parsing Error":
                self.state = job.STATUS_ERROR
                return
            # Remove the removal because of problems
            #else:
            #    os.remove('/tmp/' + file.name)

        self.settings_id.last_execution_date = datetime.datetime.now()
        # Every file is OK
        self.state = job.STATUS_ENDED
