# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

{
    'name': "Product Magazine",
    'version': '1.0',
    'depends': ['sale'],
    'author': "AbAKUS it-solutions SARL",
    'website': "http://www.abakusitsolutions.eu",
    'summary': 'Product Magazine/Journal management',
    'category': 'Sales',
    'sequence': 10,
    'description': """
Odoo Magazine Management
========================

This modules adds a way to manage Magazines and Magazines Issues in Odoo.
It adds a checkbox in the product.template to set it as Magazine, it will allow the product.product linked to be created without necesarrily having attributes.
This way, the Issues are product.product and have specific fields for magazines, like:
 * ISSN
 * ISBN
 * Issue #
 * Volume
 * Journal ID
 *  ...
It also creates a report for each product.product that can be used as labelling for storage usage.

The internal reference is auto set as following: XXXX-YYYY-ZZZZ
(where 'XXXX' is the journal ID in the Magazine (product.template), 'YYYY' is the volume of the Issue (product.product) and 'ZZZZ' is the issue number in the Issue (product.product)).
    """,
    'data': [
    		'security/security.xml',
	        'security/ir.model.access.csv',
    		'view/product_magazine_view.xml',
            'view/product_magazine_issue_view.xml',
            'report/product_label.xml',
    		],
}
