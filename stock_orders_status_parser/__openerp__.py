# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

{
    'name': 'Stock Orders Status Parser',
    'version': '8.0.1.0.1',
    'license': 'AGPL-3',
    'author': "AbAKUS it-solutions",
    'category': 'Warehouse',
    'website': 'http://www.abakusitsolutions.eu',
    'summary': 'Get orders status from text',
    'sequence': 20,
    'description': """
    """,
    'depends': [
        'stock',
         'odoo-kliemo'
    ]
    ,
    'data': [
        'wizards/stock_status_parser_wizard.xml',
    ],
    'installable': True,
}