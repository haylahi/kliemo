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

        if self.type == 'IN':
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
                #_logger.debug("== ORDER [{}]:".format(document_scanning_line))

                # Postal code
                postal_code = self.getNodeValueIfExists(order, 'PLZ')

                # Country
                str_country = self.getNodeValueIfExists(order, 'LKZ')
                country_id = False
                country_ids = self.pool.get('res.country').search(cr, uid, ['|', ('muller_country_code', '=', str_country), ('code', '=', str_country)])
                if (len(country_ids) == 0):
                    self.createAnException("Country with code {} does not exists in the database, please configure it and try again".format(str_country), 'High', None)
                    continue
                elif (len(country_ids) > 0):
                    country_id = country_ids[0]

                # Address
                str_addresses = []
                for idx in range(1, 7):
                    str_address = self.getNodeValueIfExists(order, 'ADRESSE{}'.format(idx))
                    if str_address:
                        str_addresses.append(str_address)
                #_logger.debug("== ADDRESS [{}]:".format(str_addresses))

                # Subscription number
                subscription_number = self.getNodeValueIfExists(order, 'Abonummer')

                #_logger.debug("PB : %s", pb)
                #parts_dsl = pb.match(document_scanning_line)
                #_logger.debug("PARTS : %s", parts_dsl)
                #if(parts_dsl == None or len(parts_dsl.group()) != 5):
                #    self.createAnException("Unable to parse [{}] into groups [{}]".format(document_scanning_line, parts_dsl.group()), 'High', None)
                #    continue

                # Customer number
                customer_number = document_scanning_line[document_scanning_line.find("#") + 1:document_scanning_line.rfind("#")]
                customer_number = customer_number[:customer_number.rfind("-")]

                # Customer name
                partner_name = str_addresses[0]
                #_logger.debug("== PARTNER NAME [{}]:".format(partner_name))

                # Addess
                customer_address_line_1 = ''
                customer_address_line_2 = ''
                customer_address_line_3 = ''
                # Inland or Ausland
                delivery_type = 'row'
                if ('Inland' in self.name):
                    # Inland
                    delivery_type = 'germany'
                    parts_z = pz.match(str_addresses[-1])
                    #_logger.debug("== STR_ADRESS_1 [{}]:".format(str_addresses[-1]))
                    if(parts_z is None or len(parts_z.groups()) != 2):
                        self.createAnException("Unable to parse [{}]".format(str_addresses[-1]), 'High', None)
                        continue

                    customer_postal_code = parts_z.group(1)
                    #_logger.debug("== POSTCODE [{}]:".format(customer_postal_code))
                    customer_city = parts_z.group(2)
                    #_logger.debug("== CITY [{}]:".format(customer_city))

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

                else:
                    # AUSLAND
                    _logger.debug("Len = %s", len(str_addresses))
                    if (len(str_addresses) == 6):
                        _logger.debug("== 6 ADDRESS [{}]:".format(str_addresses))
                        # No usage of str_addresses[5] because it is the country in Ausland
                        customer_postal_code = str_addresses[4][:str_addresses[4].find(' ')]
                        customer_city = str_addresses[4][str_addresses[4].find(' ') + 1:]
                        customer_address_line_3 = str_addresses[3]
                        customer_address_line_2 = str_addresses[2]
                        customer_address_line_1 = str_addresses[1]
                        partner_name = str_addresses[0]

                    if (len(str_addresses) == 5):
                        _logger.debug("== 5 ADDRESS [{}]:".format(str_addresses))
                        # No usage of str_addresses[4] because it is the country in Ausland
                        customer_postal_code = str_addresses[3][:str_addresses[3].find(' ')]
                        customer_city = str_addresses[3][str_addresses[3].find(' ') + 1:]
                        customer_address_line_2 = str_addresses[2]
                        customer_address_line_1 = str_addresses[1]
                        partner_name = str_addresses[0]

                    if (len(str_addresses) == 4):
                        _logger.debug("== 4 ADDRESS [{}]:".format(str_addresses))
                        # No usage of str_addresses[3] because it is the country in Ausland
                        customer_postal_code = str_addresses[2][:str_addresses[2].find(' ')]
                        customer_city = str_addresses[2][str_addresses[2].find(' ') + 1:]
                        customer_address_line_1 = str_addresses[1]
                        partner_name = str_addresses[0]

                    if (len(str_addresses) == 3):
                        _logger.debug("== 3 ADDRESS [{}]:".format(str_addresses))
                        # No usage of str_addresses[2] because it is the country in Ausland
                        parts_z = str_addresses[1].split(" ")
                        customer_postal_code = str_addresses[0][:str_addresses[0].find(' ')]
                        customer_city = str_addresses[0][str_addresses[0].find(' ') + 1:]
                        customer_address_line_1 = str_addresses[0]
                        partner_name = str_addresses[0]

                state_id = False
                
                # Letter Header
                letter_header = self.getNodeValueIfExists(order, 'Briefanrede')

                # Login APP
                login_app = self.getNodeValueIfExists(order, 'LoginAPP')

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
                    partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
                    # SET INFO TO PARTNER
                    partner.name = partner_name
                    partner.country_id = country_id
                    partner.state_id = state_id
                    partner.zip = customer_postal_code
                    partner.city = customer_city
                    partner.street = customer_address_line_1
                    partner.street2 = customer_address_line_2
                    partner.street3 = customer_address_line_3
                    partner.muller_customer_number = customer_number
                    partner.login_app = login_app
                    partner.letter_header = letter_header
                    check = False
                    for sub in partner.subscription_ids:
                        if int(sub.number) == int(subscription_number):
                            check = True
                            break
                    if check:
                        subscription_id = self.pool.get('muller.subscription').create(cr, uid, {
                            'partner_id': partner_id,
                            'number': subscription_number,
                        })
                
            # ------ ORDER
                _logger.debug('order')

                # Here we had a check for the existing (or not) order already,
                # but it is removed because Muller can send multiple orders with the same number
                # because it is for them split for packaging
                # So we removed this check and recreate it even if already in

                _logger.debug('Create the new picking list')
                picking_id = self.pool.get('stock.picking').create(cr, uid, {
                    'partner_id': partner_id,
                    'picking_type_id': self.job_id.settings_id.input_picking_type.id,
                    'external_order_number': document_scanning_line,
                    'file_id': int(self.id),
                    'delivery_type': delivery_type,
                })

                _logger.debug('product')
                # ------ PRODUCTS
                # Quantity
                product_quantity = float(self.getNodeValueIfExists(order, 'Menge'))

                # Issue number
                issue_number = document_scanning_line[document_scanning_line.rfind("#") + 1:document_scanning_line.rfind("*")]

                # German Post number
                german_post_id_number = int(document_scanning_line[document_scanning_line.find("*") + 1:document_scanning_line.find("#")])

                # Magazine short name
                customer_number = document_scanning_line[document_scanning_line.find("#") + 1:document_scanning_line.rfind("#")]
                magazine_short_name = customer_number[customer_number.rfind("-") + 1:]

                _logger.debug("Issue : %s | GPN : %s | MSN : %s", issue_number, german_post_id_number, magazine_short_name)

                # Test if magazine exists
                _logger.debug('test if magazine exists')
                magazine_id = self.pool.get('product.template').search(cr, uid, [('journal_id', '=', magazine_short_name)])

                # Magazine DOES NOT exist
                if not magazine_id:
                    _logger.debug('magazie does not exists')
                    self.createAnException("Magazine does not exist. SN: {}".format(magazine_short_name), "High", picking_id)
                    continue
                magazine_id = magazine_id[0]
                magazine = self.pool.get('product.template').browse(cr, uid, magazine_id)

                _logger.debug('magazine does exist')
                # Magazine DOES exist
                issue_id = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', '=', magazine_id),
                                                                                  ('issue_number', '=', issue_number),
                                                                                  ('issue_volume', '=', german_post_id_number)])
                if not issue_id:
                    self.createAnException(
                        "Issue does not exist. Issue Number in XML: {}. German Post Id in XML: {}".format(issue_number, german_post_id_number),
                            "High", picking_id)
                    continue
                issue_id = issue_id[0]

                _logger.debug('check issue info')
                # Check issue info
                issue = self.pool.get('product.product').browse(cr, uid, issue_id)

                # Create move line
                move_id = self.pool.get('stock.move').create(cr, uid, {
                    'picking_id': picking_id,
                    'product_id': issue_id,
                    'product_uom_qty': product_quantity,
                    'product_uom': magazine.uom_id.id,
                    'location_id': self.job_id.settings_id.input_picking_type.default_location_src_id.id,
                    'location_dest_id': self.job_id.settings_id.input_picking_type.default_location_dest_id.id,
                    'name': issue.name,
                })

                # Error
                if not move_id:
                    self.createAnException("Error while creating the stock move", "High", picking_id)
                    continue

                # Do the PL job: set as confirmed, check availability
                picking_obj = self.pool.get('stock.picking')
                picking = picking_obj.browse(cr, uid, [picking_id])
                picking.confirm_picking_list()
                
            # Everything went fine
            self.state = 'Parsed'

            return True

        except Exception, e:
            self.state = 'cancel'
            raise osv.except_osv(
                _("(file.createPickingListMuller) Error creating picking list for file {}".format(self.name)),
                _("Here is the error:\n %s") % tools.ustr(e))