# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
import time
import file
import logging
_logger = logging.getLogger(__name__)

class Exception(models.Model):
    LEVEL_LOW = "Low"
    LEVEL_HIGH = "High"

    STATE_WAITING = "Waiting for fix"
    STATE_FIXED = "Fixed"
    STATE_CANCELLED = "Cancelled"

    _name = 'kliemo_orders_parser.exception'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    creation_date = fields.Datetime(String="Creation date", required=True)
    level = fields.Selection([(LEVEL_LOW, LEVEL_LOW), (LEVEL_HIGH, LEVEL_HIGH)], String="Level", required=True)
    state = fields.Selection([(STATE_WAITING, STATE_WAITING), (STATE_FIXED, STATE_FIXED), (STATE_CANCELLED, STATE_CANCELLED)], default="Waiting for fix", String="State")
    message = fields.Text(String="Message")

    file_id = fields.Many2one('kliemo_orders_parser.file', ondelete='cascade', string="Reponsible file", required=True)
    picking_list_id = fields.Many2one('stock.picking', ondelete='cascade', string="Picking List")

    _defaults= {
        'creation_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    @api.multi
    def sendEmailToManager(self):
        cr = self.env.cr
        uid = self.env.user.id

        content = ""
        content += "High level Exception to be fixed:<br/><br:>"
        content += "Message: " + self.message + "<br />"
        content += "State: " + self.state + "<br/><br:>"

        system_setting_obj = self.pool.get('ir.config_parameter')
        system_setting_id = system_setting_obj.search(cr, uid, [('key', '=', 'web.base.url')])
        if system_setting_id:
            system_setting_id = system_setting_id[0]
            setting = system_setting_obj.browse(cr, uid, system_setting_id)
            content += "Link: <a href='" + setting.value + "/web#view_type=form&model=kliemo_orders_parser.exception&id=" + str(self.id) + "'>here</a>"

        mail_mail = self.pool.get('mail.mail')
        for partner in self.file_id.job_id.settings_id.manager_user:
            mail_id = mail_mail.create(cr, uid, {
                'body_html': content,
                'subject': 'WMS: High level exception during FTP parsing',
                'email_to': partner.email,
                'email_from': "odoo@abakusitsolutions.eu",
                'state': 'outgoing',
                'type': 'email',
                'auto_delete': True,
                })
            mail_mail.send(cr, uid, [mail_id])

    @api.multi
    def set_as_fixed(self):
        self.state = Exception.STATE_FIXED
        self.file_id.setAsErrorFixed()

    @api.multi
    def set_as_unfixed(self):
        self.state = Exception.STATE_WAITING
        self.file_id.setAsError()

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s: %s - %s" % (record.level, record.creation_date, record.file_id.name)))
        return result

    @api.model
    def _needaction_domain_get(self):
        return [('level', '=', 'High'), ('state', '=', Exception.STATE_WAITING)]