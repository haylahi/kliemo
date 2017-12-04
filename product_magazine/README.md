#Product Magazine management

This modules adds a way to manage Magazines and Magazines Issues in Odoo.
    It adds a checkbox in the product.template to set it as Magazine, it will allow the product.product linked to be created without necesarrily having attributes.
    This way, the Issues are product.product and have specific fields for magazines, like:
    - ISSN
    - ISBN
    - Issue #
    - Volume
    - Journal ID
    - ...
    It also creates a report for each product.product that can be used as labelling for storage usage.

    The internal reference is auto set as following: XXXX-YYYY-ZZZZ
    (where 'XXXX' is the journal ID in the Magazine (product.template), 'YYYY' is the volume of the Issue (product.product) and 'ZZZZ' is the issue number in the Issue (product.product)).
