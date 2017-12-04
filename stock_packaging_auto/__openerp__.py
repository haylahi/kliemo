# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

{
    'name': "Picking list auto packaging",
    'version': '1.0',
    'depends': ['stock', 'odoo-kliemo'],
    'author': "AbAKUS it-solutions SARL",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Warehouse',
    'sequence': 5,
    'summary': 'Packaging, shipping rules, label and reports',
    'description': """
Auto Packaging System
=====================

This module adds a mecanism on picking list to auto set information related to shipping, boxes and rules.
To do so, it uses:
 * Packages: elements with size/weight information for which the products contained in the picking list should match
 * Shipping rules: related to the destination country, the weight and some other information found in the original XML
 * Consolidator rules: related to a specific field in the XML, packages should be sent to a consolidator, which is specified by its customer number.

 All theses rules (for which data is auto set) will set a shipping rule on a picking list when confirmed and a package.
 This will have for consequence to auto assign a label (to be put on the box) with specific fields.

 Also, it inherits from the picking list report to create a new one with all these information.

""",
    'data': [
    		'security/security.xml',
	        'security/ir.model.access.csv',
    		'view/stock_picking_list_view.xml',
            'view/stock_logistic_unit_view.xml',
            'view/stock_transporter_view.xml',
            'view/stock_shipping_rule.xml',
            'view/stock_consolidator_rule.xml',
            'data/label_report_paperformat.xml',
            'data/consolidator_rules.xml',
            'data/shipping_rules.xml',
            'report/stock_packaging_reports.xml',
            'report/stock_report.xml',
            'wizard/stock_print_lists_wizard.xml',
    		],
}
