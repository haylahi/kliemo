# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class job(models.Model):
    # -----------------------------------------------------------------------
    # MODEL NAME
    _name = 'kliemo_orders_parser.job'
    _order = 'date desc'

    # -----------------------------------------------------------------------
    # MODEL FIELDS
    date = fields.Datetime(String="Date", required=True)
    settings_id = fields.Many2one('kliemo_orders_parser.ftpsettings', ondelete='cascade', string="Settings", required=True)
    state = fields.Selection([('Waiting', 'Waiting'), ('Running', 'Running'), ('Ended', 'Ended'), ('Cancelled', 'Cancelled'), ('Error', 'Error')], default='Waiting')
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
        self.state = 'Error'

    @api.multi
    def setAsErrorFixed(self):
        all_ok = True
        for file in self.files:
            if file.state == 'Parsing Error':
                self.state = 'Error'
                return
            if file.state == 'Running':
                all_ok = False
        if not all_ok:
            self.state = 'Running'
        else:
            self.state = 'Ended'

    @api.multi
    def cancel_job(self):
        self.state = 'Cancelled'

    @api.multi
    def draft_job(self):
        self.state = 'Waiting'

    @api.multi
    def run_job(self):
        return True


