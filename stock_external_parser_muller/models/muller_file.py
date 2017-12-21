# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp import models, api
from xml.dom import minidom
import openerp.tools as tools
from openerp.tools.translate import _
import logging
from openerp.osv import osv
import re


_logger = logging.getLogger(__name__)


class MullerFile(models.Model):
    # -----------------------------------------------------------------------
    # MODEL INHERIT
    _inherit = ['kliemo_orders_parser.file']

    @api.multi
    def parse_again(self):
        """
        Will parse again an order file create the linked Picking list and POA file
        Will upload the generated POA file
        """
        if self.job_id.settings_id.type != 'muller':
            return super(MullerFile, self).parse_again()

        if self.state == 'Parsing Error' or self.state == 'New':
            try:
                # set all old exceptions to cancelled
                for ex in self.exceptions:
                    if ex.state == "Waiting for fix":
                        ex.state = "Cancelled"

                # Then re-parse the file
                self.createPickingListForMuller()

            except Exception, e:
                self.state = 'Parsing Error'
                raise osv.except_osv(_("(file.parse_again) Parse file failed for %s") % self.name,
                                     _("Here is the error:\n %s") % tools.ustr(e))

            if self.state != 'Parsing Error':
                self.setAsErrorFixed()

    def createPickingListForMuller(self):
        """
        Create a Picking list based on an order file
        Generate customer if customer doesn't exist yet

        Raise an exception in case of error created
        """
        try:
            self.state = 'Parsing Error'
            cr = self.env.cr
            uid = self.env.user.id

            dom = minidom.parseString(self.content.encode('utf-8'))

            _logger.debug('parsing MULLER DOM')
            # 1. Issue number and reference
            # orders = self.getNodeValueIfExists(dom, 'Beleglesezeile')
            #_logger.debug("== FOUND [{}] orders: ".format(self.getNumberOfItems(dom, 'Datensatz')))
            orders = dom.getElementsByTagName('Datensatz')
            #pb = re.compile("^\*(.*)#(\d+-\d+-\d+)(.*)#(\d+)\*\((\d+)\)$")
            pz = re.compile("(\d+) (.*)")
            for order in orders:
                # Product / Customer Number
                document_scanning_line = self.getNodeValueIfExists(order, 'Beleglesezeile')
                _logger.debug("== ORDER [{}]:".format(document_scanning_line))

                # Quantity
                quantity = int(self.getNodeValueIfExists(order, 'Menge'))

                # Postal code
                postal_code = self.getNodeValueIfExists(order, 'PLZ')

                # Country
                str_country = self.getNodeValueIfExists(order, 'LKZ')
                country_id = False
                country_ids = self.pool.get('res.country').search(cr, uid, [('muller_country_code', '=', str_country)])
                if (len(country_ids) == 0):
                    self.createAnException("Country with code {} does not exists in the database, please configure it and try again".format(str_country), 'High', None)
                    return None
                elif (len(country_ids) > 0):
                    country_id = country_ids[0]

                # Address
                str_addresses = []
                for idx in range(1, 7):
                    str_address = self.getNodeValueIfExists(order, 'ADRESSE{}'.format(idx))
                    if str_address:
                        str_addresses.append(str_address)
                _logger.debug("== ADDRESS [{}]:".format(str_addresses))

                # Subscription number
                subscription_number = self.getNodeValueIfExists(order, 'Abonummer')

                #_logger.debug("PB : %s", pb)
                #parts_dsl = pb.match(document_scanning_line)
                #_logger.debug("PARTS : %s", parts_dsl)
                #if(parts_dsl == None or len(parts_dsl.group()) != 5):
                #    self.createAnException("Unable to parse [{}] into groups [{}]".format(document_scanning_line, parts_dsl.group()), 'High', None)
                #    return None

                # Magazine number
                magazine_number = int(document_scanning_line[document_scanning_line.find("*") + 1:document_scanning_line.find("#")])

                # Customer number
                customer_number = document_scanning_line[document_scanning_line.find("#") + 1:document_scanning_line.rfind("#")]

                # Issue number
                issue_number = int(document_scanning_line[document_scanning_line.rfind("#") + 1:document_scanning_line.rfind("*")])

                # Customer name
                partner_name = str_addresses[0]
                _logger.debug("== PARTNER NAME [{}]:".format(partner_name))

                # Addess
                customer_address_line_1 = ''
                customer_address_line_2 = ''
                customer_address_line_3 = ''
                if (self.name.index("Inland") >= 0): # Inland
                    parts_z = pz.match(str_addresses[-1])
                    _logger.debug("== STR_ADRESSE_1 [{}]:".format(str_addresses[-1]))
                    if(parts_z is None or len(parts_z.groups()) != 2):
                        self.createAnException("Unable to parse [{}]".format(str_addresses[-1]), 'High', None)
                        return None

                    customer_postal_code = parts_z.group(1)
                    _logger.debug("== POSTCODE [{}]:".format(customer_postal_code))
                    customer_city = parts_z.group(2)
                    _logger.debug("== CITY [{}]:".format(customer_city))

                if (len(str_addresses) > 2):
                    if (str_addresses[1] != str_addresses[-1]):
                        customer_address_line_1 = str_addresses[1]
                        _logger.debug("== CUSTOMER ADDRESS 1 [{}]:".format(customer_address_line_1))
                if (len(str_addresses) > 3):
                    if (str_addresses[2] != str_addresses[-1]):
                        customer_address_line_2 = str_addresses[2]
                        _logger.debug("== CUSTOMER ADDRESS 2 [{}]:".format(customer_address_line_2))
                if (len(str_addresses) > 4):
                    if (str_addresses[3] != str_addresses[-1]):
                        customer_address_line_3 = str_addresses[3]
                        _logger.debug("== CUSTOMER ADDRESS 3 [{}]:".format(customer_address_line_3))

                state_id = False
                
                # Letter Header
                letter_header = self.getNodeValueIfExists(order, 'Briefanrede')

                # Login APP
                login_app = self.getNodeValueIfExists(order, 'BLoginAPP')

                # Test if partner exists
                partner_id = self.pool.get('res.partner').search(cr, uid, [('muller_customer_number', '=', customer_number)])
                if not partner_id:
                    message = 'Partner does not exist: ' + customer_number
                    self.createAnException(message, 'Low', None)
                    # Create a partner (name, notify_email(none), customer)
                    customer_postal_code = self.getNodeValueIfExists(order, 'PLZ')
                    partner_id = self.pool.get('res.partner').create(cr, uid, {
                        'name': partner_name,
                        'notify_email': 'none',
                        'active': True,
                        'contact_address': None,
                        'country_id': country_id,
                        'state_id': state_id,
                        'zip': customer_postal_code,
                        'city': customer_city,
                        'street': customer_address_line_1,
                        'street2': customer_address_line_2,
                        'street3': customer_address_line_3,
                        'phone': None,
                        'customer': True,
                        'muller_customer_number': customer_number,
                        'login_app': login_app,
                        'letter_header': letter_header,
                    })
                    subscription_id = self.pool.get('muller.subscription').create(cr, uid, {
                        'partner_id': partner_id,
                        'number': subscription_number,
                    })
                else:
                    partner_id = partner_id[0]
                    partner = partner_obj.browse(cr, uid, partner_id)
                    # SET INFO TO PARTNER
                    partner.city = customer_city
                    partner.country_id = country_id
                    partner.state_id = state_id
                    partner.zip = customer_postal_code
                    partner.street = customer_address_line_1
                    partner.street2 = customer_address_line_2
                    partner.street3 = customer_address_line_3
                    partner.muller_customer_number = customer_number
                    partner.login_app = login_app
                    partner.letter_header = letter_header
                    check = False
                    for sub in partner.subscription_ids:
                        if sub.number == subscription_number:
                            check = True
                            break
                    if check:
                        subscription_id = self.pool.get('muller.subscription').create(cr, uid, {
                            'partner_id': partner_id,
                            'number': subscription_number,
                        })


            return
            # ------ ORDER
            _logger.debug('order')
            order_number = self.getNodeValueIfExists(dom, 'ns0:purchase-order-number')
            customer_order_number = self.getNodeValueIfExists(dom, 'ns0:end-customer-order-number')
            customer_order_number = self.removeGermanSpecialChars(str(customer_order_number))
            customer_order_text = self.getNodeValueIfExists(dom, 'ns0:end-customer-order-text')
            customer_order_text = self.removeGermanSpecialChars(str(customer_order_text))
            shipping_method = self.getNodeValueIfExists(dom, 'ns0:method')
            # because the selector on pickings is 'consolidator' and not 'collector', easier to correct it from here
            if shipping_method == 'collector':
                shipping_method = 'consolidator'

            # Test if order exists
            picking_obj = self.pool.get('stock.picking')
            picking_ids = picking_obj.search(cr, uid, [('external_order_number', '=', order_number)])

            # Picking DOES NOT EXIST, create a new one
            if not picking_ids:
                _logger.debug('picking does not exist')
                picking_id = self.pool.get('stock.picking').create(cr, uid, {
                    'partner_id': partner_id,
                    'picking_type_id': self.job_id.settings_id.input_picking_type.id,
                    'external_order_number': order_number,
                    'customer_order_number': customer_order_number,
                    'customer_order_text': customer_order_text,
                    'shipping_method': shipping_method,
                    'file_id': int(self.id),
                    'po_box': customer_po_box,
                })

            # Picking DOES EXISTS
            else:
                picking_id = picking_ids[0]
                picking = picking_obj.browse(cr, uid, picking_id)  # get the first one
                if picking.state != 'draft':  # Check the state of the picking
                    _logger.debug('picking exists and is not in draft anymore')
                    self.state = 'Parsed'
                    self.createAnException("Picking list already exists: {}".format(order_number), "Low", picking_id)
                    return None
                # Picking DOES EXISTS, simply update it
                else:
                    _logger.debug("picking exists and is in draft, we will update it")

            _logger.debug('product')
            # ------ PRODUCTS
            number_of_products = self.getNumberOfItems(dom, 'ns0:purchase-order-item')
            for orderItem in dom.getElementsByTagName('ns0:purchase-order-item'):
                _logger.debug(orderItem)
                item_number = self.getNodeValueIfExists(orderItem, 'ns0:item-number')
                product_quantity = float(self.getNodeValueIfExists(orderItem, 'ns0:quantity'))
                issue_id = self.getNodeValueIfExists(orderItem, 'ns0:issue-id-start')
                volume_id = self.getNodeValueIfExists(orderItem, 'ns0:volume-id-start')
                wbs_element = self.getNodeValueIfExists(orderItem, 'ns0:wbs-element')
                periodical_permit_number = self.getNodeValueIfExists(orderItem, 'ns0:periodical-permit-number')
                journal_id = self.getNodeValueIfExists(orderItem, 'ns0:journal-id')
                issue_type = self.getNodeValueIfExists(orderItem, 'ns0:issue-type')
                issue_title = self.getNodeValueIfExists(orderItem, 'ns0:title')
                weight = self.getNodeValueIfExists(orderItem, 'ns0:net-weight-kg')

                # Test if magazine exists
                _logger.debug('test if magazine exists')
                magazine_id = self.pool.get('product.template').search(cr, uid, [('journal_id', '=', journal_id)])

                # Magazine DOES NOT exist
                if not magazine_id:
                    _logger.debug('magazie does not exists')
                    self.createAnException("Magazine does not exist. Journal ID: {}".format(journal_id), "High",
                                           picking_id)
                    return None
                magazine_id = magazine_id[0]
                magazine = self.pool.get('product.template').browse(cr, uid, magazine_id)

                _logger.debug('magazine does exist')
                # Magazine DOES exist
                issue_type = 'special' if issue_type == 'supplement' else issue_type  # error between 'supplement' and 'special'
                issue_id2 = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', '=', magazine_id),
                                                                              ('issue_number', '=', issue_id),
                                                                              ('issue_volume', '=', volume_id),
                                                                              ('issue_type', '=', issue_type)])
                if not issue_id2:
                    self.createAnException(
                        "Issue does not exist. Issue ID in XML: {}. Volume ID in XML: {}".format(issue_id, volume_id),
                        "High", picking_id)
                    return None
                issue_id = issue_id2[0]

                _logger.debug('check issue info')
                # Check issue info
                issue = self.pool.get('product.product').browse(cr, uid, issue_id)

                _logger.debug('volume check')
                # Volume check
                if issue.issue_volume != volume_id:
                    self.createAnException(
                        "Issue volume is different in XML and in Odoo. XML: {} . Odoo: {}".format(volume_id,
                                                                                                  issue.issue_volume),
                        "High", picking_id)
                    return None

                # Type check
                _logger.debug('type check')
                if issue.issue_type != issue_type:
                    self.createAnException(
                        "Issue type is different in XML and in Odoo. XML: {} . Odoo: {}".format(issue_type,
                                                                                                issue.issue_type),
                        "Low", picking_id)
                    # return None

                # Checks OK
                _logger.debug('checks are ok')
                # Set weight

                issue.weight_net = float(weight) / product_quantity
                # Set the WBS element as the title
                magazine.title = str(wbs_element)

                # Create move line
                move_id = self.pool.get('stock.move').create(cr, uid, {
                    'picking_id': picking_id,
                    'product_id': issue_id,
                    'product_uom_qty': product_quantity,
                    'product_uom': magazine.uom_id.id,
                    'location_id': self.job_id.settings_id.input_picking_type.default_location_src_id.id,
                    'location_dest_id': self.job_id.settings_id.input_picking_type.default_location_dest_id.id,
                    'name': issue.name,
                    'item_number': item_number,
                })

                # Error
                if not move_id:
                    self.createAnException("Error while creating the stock move", "High", picking_id)
                    return None

            # Everything went fine
            self.state = 'Parsed'

            # Do the PL job: set as confirmed, check availability, print
            picking_obj = self.pool.get('stock.picking')
            picking = picking_obj.browse(cr, uid, [picking_id])
            picking.confirm_picking_list()

            return poa_file_id

        except Exception, e:
            self.state = 'cancel'
            raise osv.except_osv(
                _("(file.createPickingListMuller) Error creating picking list for file {}".format(self.name)),
                _("Here is the error:\n %s") % tools.ustr(e))