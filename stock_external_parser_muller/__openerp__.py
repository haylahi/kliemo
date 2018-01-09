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
        'odoo-kliemo',
        'stock_packaging_auto',
    ],
    'sequence': 1,
    'data': [
        'wizards/stock_muller_daily_orders_report.xml',
        'views/ftp_settings_view.xml',
        'views/res_country_view.xml', 
        'views/res_partner_view.xml',
        'views/stock_picking_view.xml',
        'views/res_menu.xml',
        'views/stock_shipping_rule.xml',

        'data/res_countries.xml',
        'data/shipping_rules.xml',
    ],
}