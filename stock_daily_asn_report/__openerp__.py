# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

{
    'name': 'ASN Excel Daily Report',
    'version': '8.0.1.0',
    'license': 'AGPL-3',
    'author': "AbAKUS it-solutions",
    'category': 'Warehouse',
    'website': 'http://www.abakusitsolutions.eu',
    'summary': 'ASN Report in EXCEL',
    'sequence': 20,
    'description': """
ASN Excel Daily Report
======================

This modules creates a new Excel report for ASN (Advanced Shipping Notification) for picking list in a daily basis.

A new menuitem appears in the warehouse menu that allows to select a FTP setting (if none, it will take all the picking) and a date.
The system will put in the file all the pickings marked as 'done' for the selected date and set all the information as explained in the original ASN document.

It also creates a CRON task that should send by email and upload to the FTP server the Report.
(Still under dev)

Requires: 'report_xls' module, developed by the OCA.
    """,
    'depends': ['stock', 'report_xls', 'odoo-kliemo'],
    'data': [
        'wizard/stock_picking_daily_report_wizard.xml',
        'cron_tasks.xml',
        'asn_email_template.xml',
    ],
    'installable': True,
}
