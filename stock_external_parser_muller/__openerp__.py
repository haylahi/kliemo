# -*- encoding: utf-8 -*-
# This code (c) 2017 - AbAKUS it-solutions
#

{
    'name': "Müller Parser",

    'description': """
MULLER Parser
==========================
    """,
    'author': "Paul Ntabuye Butera and Valentin Thirion @ AbAKUS it-solutions",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'warehouse',
    'version': '1.0',
    'depends': [
        'odoo-kliemo'
    ],
    'sequence': 1,
    'data': [
        'views/ftp_settings_view.xml',
        'views/res_country_view.xml', 
        'data/res_countries.xml', 
    ],
}