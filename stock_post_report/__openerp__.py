# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

{
    'name': 'SPRINGER : Stock POST Daily Report',
    'version': '8.0.1.0',
    'license': 'AGPL-3',
    'author': "AbAKUS it-solutions",
    'category': 'Warehouse',
    'website': 'http://www.abakusitsolutions.eu',
    'summary': 'Streifband POST Reports in EXCEL',
    'sequence': 20,
    'description': """
POST Daily Report
======================

This modules creates a new Excel report for POST (Streifband deliveries) for picking list in a daily basis.

A new menuitem appears in the warehouse menu that allows to select a FTP setting (if none, it will take all the picking) and a date.
The system will put in the file all the pickings marked as 'done' for the selected date, the 'Streifband delivery rule' and present the different delivery weights by group and amount.

Requires: 'report_xls' module, developed by the OCA.
    """,
    'depends': [
        'stock_external_parser_springer'
    ],
    'data': [
        'wizard/stock_post_report_wizard.xml',
        'report/stock_post_report.xml',
    ],
    'installable': True,
}
