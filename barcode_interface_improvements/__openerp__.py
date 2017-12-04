# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

{
   'name': "Barcode interface Improvements",
    'version': '1.0',
    'depends': ['stock', 'odoo-kliemo', 'product_magazine', 'stock_packaging_auto'],
    'author': "Valentin THIRION, Bernard DELHEZ, AbAKUS it-solutions SARL",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'Warehouse Management',
    'sequence': 15,
    'summary': 'New menus, new fields and ergonomic improvements.',
    'description':
"""
Barcode Interface Improvements
==============================

This modules adds new fields, menus and views to the original barcode interface.

Menu:
 * Quit button everywhere
 * Search field
 * Incomming pickings direct access
 * Outgoing pickings direct access

Fields:
 * Pickings OUT: all the fields comming from the XML files
 * Picking OUT: product/magazine fields from product.magazine

Buttons:
 * Print labels for move line
 * Print picking report

 Some other functions are also implemented in order to improve this interface.
    """,
    'data': ['view/stock.xml'],
    'qweb': ['static/src/xml/picking_improvements.xml'],
}