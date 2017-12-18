# -*- encoding: utf-8 -*-
# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2017

from openerp.addons.document.document import nodefd_static
from thread import _local
from openerp import models, fields, api
from lxml import etree
from xml.dom import minidom
import openerp.tools as tools
from openerp.osv import osv
from openerp.tools.translate import _
import datetime
from zipfile import ZipFile
import os
import time
import logging
from openerp.osv import osv
_logger = logging.getLogger(__name__)


class SpringerFileFile(models.Model):
    # -----------------------------------------------------------------------
    # MODEL INHERIT
    _inherit = ['kliemo_orders_parser.file']

    @api.model
    def _type_selection(self):
        selection = super(SpringerFileFile, self)._type_selection()
        selection.append(('POA', 'POA'))
        selection.append(('ASN', 'ASN'))
        selection.append(('STOCK', 'Stock'))
        return selection
    type = fields.Selection(_type_selection, string='Type', required=True)
    uploaded = fields.Boolean(string="Correctly uploaded", default=False)

    @api.multi
    def parse_again(self):
        """
        Will parse again an order file create the linked Picking list and POA file
        Will upload the generated POA file
        """
        if self.job_id.settings_id.type != 'springer':
            return super(SpringerFileFile, self).parse_again()

        if self.state == 'Parsing Error' or self.state == 'New':
            try:
                # set all old exeptions to cancelled
                for exce in self.exceptions:
                    if exce.state == "Waiting for fix":
                        exce.state = "Cancelled"

                # Then re-parse the file
                poa_file_ids = []
                file_poaid = self.createPickingList()
                poa_file_ids.append(file_poaid)

                # for each POA, upload them
                if len(poa_file_ids) > 0:
                    self.job_id.settings_id.upload_files(poa_file_ids, 'POA')

            except Exception, e:
                self.state = 'Parsing Error'
                raise osv.except_osv(_("(file.parse_again) Parse file failed for %s") % self.name, _("Here is the error:\n %s") % tools.ustr(e))

            if self.state != 'Parsing Error':
                self.setAsErrorFixed()

    def createPickingList(self):
        """
        Create a Picking list based on an order file
        Generate a POA linked to the Picking list
        Generate customer if customer doesn't exist yet

        Returns the POA file id or None if an exception is created
        """
        try:
            self.state = 'Parsing Error'
            cr = self.env.cr
            uid = self.env.user.id

            dom = minidom.parseString(self.content.encode('utf-8'))

            _logger.debug('parsing DOM')
            # ------ CHECK PURCHASE ORDER CORRECTNESS
            # Delivery method should be the same as set in FTP settings
            delivery_method = self.getNodeValueIfExists(dom, 'ns0:delivery-method')
            # TODO check if it works as expected
            if delivery_method != self.job_id.settings_id.delivery_method and self.job_id.settings_id.delivery_method != 'both':
                self.createAnException("Delivery method not correct. Expected: '{}'. Received:'{}'".format(self.job_id.settings_id.delivery_method,delivery_method), 'High', None)
                return None
            _logger.debug('delivery method parsed')

            # Service provider should be the same as set in FTP settings
            service_provider = self.getNodeValueIfExists(dom, 'ns0:provider')
            if service_provider != self.job_id.settings_id.service_provider:
                self.createAnException("Service provider method not correct. Expected: '{}'. Received:'{}'".format(self.job_id.settings_id.service_provider,service_provider), 'High', None)
                return None
            _logger.debug('service provider parsed')

            # Service type shoud be the same as set in FT settings
            service_type = self.getNodeValueIfExists(dom, 'ns0:type')
            if service_type != self.job_id.settings_id.service_type:
                self.createAnException("Service type method not correct. Expected: '{}'. Received:'{}'".format(self.job_id.settings_id.service_type,service_type), 'High', None)
                return None
            _logger.debug('service type  parsed')

            # ------ PARTNER
            endorsement_line_1 = str(self.getNodeValueIfExists(dom, 'ns0:endorsement-line1'))
            endorsement_line_2 = str(self.getNodeValueIfExists(dom, 'ns0:endorsement-line2'))
            # Name 1
            partner_name = str(self.getNodeValueIfExists(dom, 'ns0:name1'))
            if partner_name == "":
                partner_name = str(self.getNodeValueIfExists(dom, 'ns0:line1'))
            customer_address_line_1 = ''
            customer_address_line_2 = ''
            customer_address_line_3 = ''
            # Name 2
            if (self.getNodeValueIfExists(dom, 'ns0:name2')):
                customer_address_line_1 = str(self.getNodeValueIfExists(dom, 'ns0:name2'))
            # Name 2 second
            elif (self.getNodeValueIfExists(dom, 'ns0:line2')):
                customer_address_line_1 = str(self.getNodeValueIfExists(dom, 'ns0:line2'))
            # Name 3
            if (self.getNodeValueIfExists(dom, 'ns0:line3')):
                customer_address_line_2 = str(self.getNodeValueIfExists(dom, 'ns0:line3'))

            customer_id = self.getNodeValueIfExists(dom, 'ns0:customer-id')
            customer_city = self.getNodeValueIfExists(dom, 'ns0:city')
            customer_postal_code = self.getNodeValueIfExists(dom, 'ns0:postal-code')
            customer_state = self.getNodeValueIfExists(dom, 'ns0:state')
            customer_country_code = self.getNodeValueIfExists(dom, 'ns0:country-code')
            customer_address_line_3 = "{} {}".format(self.getNodeValueIfExists(dom, 'ns0:street'), self.getNodeValueIfExists(dom, 'ns0:street-number1'))
            customer_po_box = "{}".format(self.getNodeValueIfExists(dom, 'ns0:po-box'))
            customer_phone = self.getNodeValueIfExists(dom, 'ns0:phone')

            # Test if address line 2 is "street + number"
            if customer_address_line_1.replace(" ", "") == customer_address_line_3.replace(" ", ""):
                customer_address_line_3 = "" 
            
            # Test if address line 2 is "postal + city"
            postal_code_and_city = customer_postal_code + " " + customer_city
            if customer_address_line_2 == postal_code_and_city:
                customer_address_line_2 = ""

            
            _logger.debug('customer parsed')

            #content = StringIO.StringIO(str(self.content))
            #tree = etree.parse(content)
            #ns = {'ns0': 'http://devel.springer.de/fulfillment/mps/schema/'}
            #partner_name = tree.find('/ns0:purchase-order-header/ns0:delivery-address/ns0:name1', ns).text

            # Country
            country_id = self.pool.get('res.country').search(cr, uid, [('code', '=', customer_country_code)])
            if country_id:
                country_id = country_id[0]
            else:
                # CREATE EXCEPTION
                self.createAnException("Country does not exists", 'High', None)
                return None
            _logger.debug('country parsed')

            # State
            if customer_state != "":
                state_id = self.pool.get('res.country.state').search(cr, uid, [('country_id', '=', country_id), ('code', '=', customer_state)])
                if state_id:
                    state_id = state_id[0]
                else:
                    # CREATE AN EXCEPTION
                    self.createAnException("State does not exists", 'Low', None)
            _logger.debug('state parsed')

            _logger.debug('test if partner exists')
            # Test if partner exists
            partner_obj = self.pool.get('res.partner')
            partner_id = partner_obj.search(cr, uid, [('customer_number', '=', customer_id)])
            # Partner DOES NOT exist
            if not partner_id:
                message = 'Partner does not exist: ' + customer_id
                self.createAnException(message, 'Low', None)
                # Create a partner (name, notify_email(none), customer)
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
                    'phone': customer_phone,
                    'customer': True,
                    'customer_number': customer_id,
                    'endorsement_line_1': endorsement_line_1,
                    'endorsement_line_2': endorsement_line_2,
                })
            # Partner EXISTS, set info
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
                partner.endorsement_line_1 = endorsement_line_1
                partner.endorsement_line_2 = endorsement_line_2
                partner.phone = customer_phone

            _logger.debug('order')
            # ------ ORDER
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
                picking = picking_obj.browse(cr, uid, picking_id) # get the first one
                if picking.state != 'draft': # Check the state of the picking
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
                    self.createAnException("Magazine does not exist. Journal ID: {}".format(journal_id), "High", picking_id)
                    return None
                magazine_id = magazine_id[0]
                magazine = self.pool.get('product.template').browse(cr, uid, magazine_id)

                _logger.debug('magazine does exist')
                # Magazine DOES exist
                issue_type = 'special' if issue_type == 'supplement' else issue_type # error between 'supplement' and 'special'
                issue_id2 = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', '=', magazine_id), ('issue_number', '=', issue_id), ('issue_volume', '=', volume_id), ('issue_type', '=', issue_type)])
                if not issue_id2:
                    self.createAnException("Issue does not exist. Issue ID in XML: {}. Volume ID in XML: {}".format(issue_id, volume_id), "High", picking_id)
                    return None
                issue_id = issue_id2[0]

                _logger.debug('check issue info')
                # Check issue info
                issue = self.pool.get('product.product').browse(cr, uid, issue_id)

                _logger.debug('volume check')
                # Volume check
                if issue.issue_volume != volume_id:
                    self.createAnException("Issue volume is different in XML and in Odoo. XML: {} . Odoo: {}".format(volume_id, issue.issue_volume), "High", picking_id)
                    return None

                # Type check
                _logger.debug('type check')
                if issue.issue_type != issue_type:
                    self.createAnException("Issue type is different in XML and in Odoo. XML: {} . Odoo: {}".format(issue_type, issue.issue_type), "Low", picking_id)
                    #return None

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

            # Write back the POA file
            _logger.debug("Create POA file")
            poa_file_id = self.writePOAFile(picking_id)

            if not poa_file_id:
                self.createAnException("Error while creating the POA", "High", picking_id)
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
            raise osv.except_osv(_("(file.createPickingList) Error creating picking list for file {}".format(self.name)), _("Here is the error:\n %s") % tools.ustr(e))

    @api.multi
    def writePOAFile(self, picking_id):
        """
        This method will get the POA representation from Picking and create file
        """
        cr = self.env.cr
        uid = self.env.user.id

        picking_obj = self.pool.get('stock.picking')
        picking = picking_obj.browse(cr, uid, [picking_id])
        poa_content = picking.get_poa_representation()

        # filename
        filename = "poa_mps_" + picking.external_order_number + ".xml"

        # create OUT file
        file_id = self.pool.get('kliemo_orders_parser.file').create(cr, uid, {
            'type': 'POA',
            'job_id': self.job_id.id,
            'creation_date': datetime.datetime.now(),
            'name': filename,
            'content': poa_content,
            'state': 'Parsed',
        })

        _logger.debug("poa file created %s", (file_id))

        # return its ID
        return file_id

    @api.multi
    def writeASNFile(self, picking_id):
        """
        This method will get the POA representation from Picking and create file
        """
        cr = self.env.cr
        uid = self.env.user.id

        picking_obj = self.pool.get('stock.picking')
        picking = picking_obj.browse(cr, uid, [picking_id])
        asn_content = picking.get_asn_representation()

        # filename
        filename = "asn_mps_" + picking.external_order_number + ".xml"

        # create OUT file
        file_id = self.pool.get('kliemo_orders_parser.file').create(cr, uid, {
            'type': 'ASN',
            'job_id': picking.file_id.job_id.id,
            'creation_date': datetime.datetime.now(),
            'name': filename,
            'content': asn_content[0],
            'state': 'Parsed',
        })

        _logger.debug("asn file created %s", (file_id))

        # return its ID
        return file_id