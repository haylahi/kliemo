# -*- coding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

import logging
from openerp import models
import datetime
from openerp.osv import osv
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class ftp_settings(models.Model):
    _inherit = ['kliemo_orders_parser.ftpsettings']

    def _cron_create_asn_report_send_and_upload(self, cr, uid, ids=None, context=None):
        # Get all FTP settings
        settings_ids = self.pool.get('kliemo_orders_parser.ftpsettings').search(cr, uid, ['&', ('active','=',True), ('type', '=', 'springer')])
        if (len(settings_ids)) == 0:
            raise osv.except_osv(_("No parser for Springer is active"), _("You have to enable a parser for type 'springer' to do that"))
            
        for setting_id in settings_ids:
            # Get the setting
            setting = settings_obj.browse(cr, uid, setting_id)
            # create report
            report = self.get_report(setting_id) # TODO: report not OK
            #report = report.encode('base64')

            # send it by email
            content = ""
            content += "ASN REPORT<br/><br:>"
            mail_mail = self.pool.get('mail.mail')
            for user in setting.manager_user:
                _logger.debug("SEND email to: %s", user.email)
                # Create the mail
                mail_id = mail_mail.create(cr, uid, {
                    'body_html': content,
                    'subject': 'WMS: ASN Daily report',
                    'email_to': user.email,
                    'email_from': "odoo@abakusitsolutions.eu",
                    'state': 'outgoing',
                    'type': 'email',
                    'auto_delete': False,
                    })

                # Add the attachment
                attachment_ids = []
                attachment_data = {
                    'name': report['report_name'],
                    'datas_fname': report['type'],
                    'datas': report['datas'],
                    'res_model': mail_mail._name,
                    'res_id': mail_id,
                }
                #attachment_ids.append(self.pool.get('ir.attachment').create(cr, uid, attachment_data, context=context))
                #if attachment_ids:
                #    mail_mail.write(cr, uid, mail_id, {'attachment_ids': [(6, 0, attachment_ids)]}, context=context)
                mail_mail.write(cr, uid, mail_id, {'attachment_ids': [(6, 0, [report])]}, context=context)
                mail_mail.send(cr, uid, [mail_id])

            # upload it to the server

    def get_report(self, setting_id):
        # Date
        date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")

        # get the report for this setting
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'stock.picking.asn.xls',
            'datas': {
                'model': 'stock.picking',
                'report_date': date,
                'ftp_setting': setting_id,
                'ids': None,
            }
        }


