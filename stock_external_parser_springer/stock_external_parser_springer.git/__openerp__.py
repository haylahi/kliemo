# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

{
    'name': "Springer Parser",

    'description': """
SPRINGER Parser
==========================

This modules will do the following actions:
 * Implement an FTP connector with parameters (in a configuration menu) that will be ran each hour
 * This connector will get files from the FTP server and parse them
 * It will automatically create Picking lists for the files, also create partners in the case they don’t exists
 * In the case there is a problem, it will create a ‘input exception’, kind of data that present the parsed data and the problem it had (‘product not recognized’, ‘unknown partner’ …). These exceptions will be set with two levels of emergency (normal: exception handled by the system, error: exception not handled, need for an intervention, send an email to the responsible).
 * It will also create, for each OUT delivery, an XML file that will be sent to the FTP server

Tasks:
 * A cron task is ran each day to fetch new orders
 * A cron task removed the old files in the system (> 30 days)
 * It auto creates a POA file when picking lists are created
 * It auto creates an ASN file when picking lists are transferred
 * It auto creates customers when not existing
 * It auto sends an email to the 'managers' when a problem occurs during parsing
 * It allows the users to handle parsing exception, edit the file and parse again
    """,
    'author': "Valentin Thirion @ AbAKUS it-solutions",
    'website': "http://www.abakusitsolutions.eu",
    'category': 'warehouse',
    'version': '1.0',
    'depends': [
        'stock',
        'sale',
        'odoo-kliemo'
    ],
    'sequence': 1,
    'data': [
        'views/ftp_settings_view.xml',
        # 'security/ir.model.access.csv',
        #'views/ftpSettings.xml',
        #'views/job.xml',
        #'views/file.xml',
        #'views/exception.xml',
        #'views/partner.xml',
        #'views/picking_list.xml',
        #'cron_tasks.xml',
    ],
}