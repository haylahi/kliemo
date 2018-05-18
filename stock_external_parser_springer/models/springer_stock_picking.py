# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
from lxml import etree
import datetime
import logging

_logger = logging.getLogger(__name__)


class SpringerPicking(models.Model):
    _inherit = ['stock.picking']

    # -----------------------------------------------------------------------
    # MODEL FIELDS
    customer_order_number = fields.Char(string="Customer Order Number")
    customer_order_text = fields.Char(string="Customer Order Text")
    asn_date = fields.Datetime(string="ASN Date", readonly=False)
    asn_done = fields.Boolean(string="ASN", default=False)
    tat = fields.Integer(string="TAT")
    shipping_method = shipping_method = fields.Selection([('standard', 'Standard'), ('courier', 'Courier'), ('consolidator', 'Collector')], string="Shipping method",)
    asn_file_id = fields.Many2one('kliemo_orders_parser.file', string="ASN File")
    po_box = fields.Char(string="PO-Box")
    postal_permit_number = fields.Char(string="Postal Permit #")
    ads = fields.Char(string="ADS")
    delivery_method = fields.Selection([('initial', 'initial'), ('subsequent', 'subsequent')], string="Delivery Method")

    # -----------------------------------------------------------------------
    # ODOO INHERIT METHODS
    @api.one
    def do_transfer(self):
        picking_ids = (self.ids,)
        if self.settings_type == 'springer':
            self.createASNFile()
        super(SpringerPicking, self).do_transfer()
        _logger.debug('Picking list print report on transfer')
        return self.print_labels()
        #return self.pool['report'].get_action(self.env.cr, self.env.uid, self.id, 'stock_packaging_auto.base_label_report', context=self.env.context) # print the labels

    # -----------------------------------------------------------------------
    # MODEL METHODS

    # Used as an interface
    @api.multi
    def confirm_picking_list(self):
        for picking in self:
            if picking.settings_type != 'springer':
                super(SpringerPicking, picking).confirm_picking_list()
                continue

            auto_set_ok = True
            if (picking.shipping_rule == False):
                auto_set_ok = False
            # auto set rule if not already set
            if(picking.file_id and not auto_set_ok): 
                try:
                    # auto set package
                    picking.compute_shipping()
                    auto_set_ok = True
                except Exception, e:
                    _logger.debug("ERROR OF COMPUTING PACKAGING OR PICKING AUTO")
                    picking.file_id.setAsError()

            # confirm the PL
            if auto_set_ok:
                picking.action_confirm()
                picking.action_assign()
                picking.print_list() # print the PL

    @api.multi
    def get_poa_representation(self):
        cr = self.env.cr
        uid = self.env.user.id

        # ---- POA
        nsmap = {
            None:'http://www.crossmediasolutions.de/GPN/springer/po-1.9',
            "xsi":"http://www.w3.org/2001/XMLSchema-instance",
                 }
        poaxml = etree.Element("purchase-order-acknowledgement", nsmap=nsmap)
        poaxml.attrib['{{{pre}}}schemaLocation'.format(pre="http://www.w3.org/2001/XMLSchema-instance")] =  "http://www.crossmediasolutions.de/GPN/springer/po-1.9 http://www.crossmediasolutions.de/schemas/spr/poa_1-9-7.xsd"


        # ---- POA-HEADER
        poaHeader = etree.SubElement(poaxml, "poa-header")

        node = etree.Element("ordering-site")
        node.text = 'mps'
        poaHeader.append(node)
        node = etree.Element("purchase-order-number")
        # User item order number if initial mode
        if self.delivery_method == 'initial':
            if len(self.move_lines) > 0:
                node.text = self.move_lines[0].item_number
            else:
                node.text = self.external_order_number
        else:
            node.text = self.external_order_number
        poaHeader.append(node)
        node = etree.Element("customer-id")
        node.text = self.partner_id.customer_number
        poaHeader.append(node)
        node = etree.Element("poa-date")
        node.text = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S %Z")
        poaHeader.append(node)
        # ----

        # ---- POA-ITEM
        for move in self.move_lines:
            poaItem = etree.SubElement(poaxml, "poa-item")
            node = etree.Element("item-number")
            node.text = move.item_number
            poaItem.append(node)
            node = etree.Element("ordered-quantity")
            node.text = str(move.product_uom_qty)
            poaItem.append(node)
            action = etree.Element("action")
            action.text = 'accepted'
            poaItem.append(action)

            for product in move.product_id:
                if self.pool.get('product.product').browse(cr, uid, product.id).qty_available < move.product_uom_qty:
                    action.text = 'rejected'
                    break

            # issue-ref
            issue_node = etree.Element("issue-ref")
            node = etree.Element("journal-id")
            node.text = move.product_id.product_tmpl_id.journal_id
            issue_node.append(node)
            node = etree.Element("volume-id-start")
            node.text = move.product_id.issue_volume
            issue_node.append(node)
            node = etree.Element("issue-id-start")
            node.text = move.product_id.issue_number
            issue_node.append(node)
            node = etree.Element("issue-type")
            node.text = 'supplement' if move.product_id.issue_type == 'special' else move.product_id.issue_type # error between 'supplement' and 'special'
            issue_node.append(node)

            poaItem.append(issue_node)

            if action.text == "rejected":
                _logger.debug("ORDER REJECTED")
                self.file_id.createAnException("Order rejected: stock too low", "Low", self.id)
        # ----

        # create string from XML
        content = etree.tostring(poaxml, pretty_print=True)

        return content

    @api.one
    def get_asn_representation(self):
        # ---- ASN
        nsmap = {
            None:'http://www.crossmediasolutions.de/GPN/springer/po-1.9',
            "xsi":"http://www.w3.org/2001/XMLSchema-instance",
                 }
        asnxml = etree.Element("advanced-shipping-notification", nsmap=nsmap)
        asnxml.attrib['{{{pre}}}schemaLocation'.format(pre="http://www.w3.org/2001/XMLSchema-instance")] =  "http://www.crossmediasolutions.de/GPN/springer/po-1.9 http://www.crossmediasolutions.de/schemas/spr/asn_1-9-7.xsd"

        # ---- ASN-HEADER
        asnHeader = etree.SubElement(asnxml, "asn-header")

        node = etree.Element("purchase-order-number")
        node.text = self.external_order_number
        asnHeader.append(node)
        node = etree.Element("euradius-order-number") #TODO or sheridan-order-number or kliemo-order-number (addto xsd file)
        node.text = self.name #TODO check if picking name
        asnHeader.append(node)
        """
        node = etree.Element("kliemo-order-number")
        node.text = self.name
        poaHeader.append(node)
        """
        node = etree.Element("production-plant")
        node.text = "kliemo"
        asnHeader.append(node)
        node = etree.Element("shipment-date")
        node.text = datetime.datetime.now().strftime("%Y-%m-%d")
        asnHeader.append(node)
        node = etree.Element("shipment-method")
        node.text = str(self.shipping_rule.service)
        asnHeader.append(node)

        if len(self.boxes) > 0:
            for box in self.boxes:
                node = etree.Element("tracking-number")
                node.text = box.tracking_number if (box.tracking_number) else ''
                asnHeader.append(node)

        node = etree.Element("net-weight-kg")
        node.text = str(self.net_picking_weight)
        asnHeader.append(node)
        node = etree.Element("gross-weight-kg")
        node.text = str(self.total_picking_weight)
        asnHeader.append(node)
        node = etree.Element("number-of-boxes")
        node.text = str(self.logistic_unit_quantity)
        asnHeader.append(node)
        node = etree.Element("delivery-number")
        node.text = self.name
        asnHeader.append(node)
        # ----

        # ---- ASN-ITEM
        for move in self.move_lines:
            asnitem = etree.SubElement(asnxml, "asn-item")

            node = etree.Element("item-number")
            node.text = str(move.item_number)
            asnitem.append(node)

            node = etree.Element("shipped-quantity")
            node.text = str(int(move.product_uom_qty))
            asnitem.append(node)

            # issue-ref
            if move.product_id.is_magazine:
                issue_node = etree.Element("issue-ref")
                node = etree.Element("journal-id")
                node.text = move.product_id.product_tmpl_id.journal_id
                issue_node.append(node)
                node = etree.Element("volume-id-start")
                node.text = move.product_id.issue_volume
                issue_node.append(node)
                node = etree.Element("issue-id-start")
                node.text = move.product_id.issue_number
                issue_node.append(node)
                node = etree.Element("issue-type")
                node.text = 'supplement' if move.product_id.issue_type == 'special' else move.product_id.issue_type # error between 'supplement' and 'special'
                issue_node.append(node)
                asnitem.append(issue_node)
            else:
                book_node = etree.Element("book-ref")
                node = etree.Element("ean")
                node.text = move.product_id.ean13
                book_node.append(node)
                asnitem.append(book_node)

            node = etree.Element("customer-order-number")
            node.text = str(self.customer_order_number)
            asnitem.append(node)

            # TODO delivery-item-number in future
        # ----

        # create string from XML
        content = etree.tostring(asnxml, pretty_print=True)

        return content

    @api.one
    def createASNFile(self):
        if self.file_id:
            _logger.debug("{} will create asn file".format(self.id))
            asn_id = self.file_id.writeASNFile(self.id)
            self.asn_file_id = asn_id
            self.asn_date = self.asn_file_id.creation_date

    # This method will fetch the correct shipping rule for the current picking list
    @api.multi
    def compute_shipping(self):
        for picking in self:
            # If not Springer, pass to the upper level
            if picking.settings_id.type != 'springer':
                super(SpringerPicking, picking).compute_shipping()
                continue

            # init
            picking._compute_gross_weight()
            picking.compute_packaging()
            picking.logistic_unit_quantity = 0
            picking.shipping_rule = None
            picking.logistic_unit_report = None

            if not picking.file_id:
                raise osv.except_osv(_("Error"), _("Can not get auto shipping because this picking list is not linked to a  file."))

            # Shipping rule is 'consolidator'
            if picking.shipping_method == 'consolidator':
                # Assign shipping rule
                rules_obj = self.pool.get('stock.shipping_rule')
                rules_id = rules_obj.search(self.env.cr, self.env.uid, [])
                for rule in rules_obj.browse(self.env.cr, self.env.uid, rules_id):
                    if rule.shipping_method == 'consolidator':
                        picking.shipping_rule = rule.id
                        break

                if not picking.shipping_rule:
                    raise osv.except_osv(_("Error"), _("Can not get auto shipping rule because no shipping rule for collector is defined."))

                # Get consolidator rule
                # check customer number
                if not picking.partner_id.customer_number:
                    raise osv.except_osv(_("Error"), _("Can not get auto collector rule because no customer number on this partner."))

                rules_obj = self.pool.get('stock.consolidator_rule')
                rules_id = rules_obj.search(self.env.cr, self.env.uid, [])
                for rule in rules_obj.browse(self.env.cr, self.env.uid, rules_id):
                    if rule.customer_numbers and    picking.partner_id.customer_number in rule.customer_numbers:
                        picking.consolidator_rule = rule.id
                        break

                # label quantity
                picking.logistic_unit_quantity = 1

                if not picking.consolidator_rule:
                    raise osv.except_osv(_("Error"), _("Can not get auto collector rule because customer number in any consolidator rule."))
                return

            # get shipping rules
            rules_obj = self.pool.get('stock.shipping_rule')
            rules = rules_obj.search(self.env.cr, self.env.uid, [], order='priority asc')

            # error, no rules
            if len(rules) < 1:
                raise osv.except_osv(_("Error"), _("There is no shipping rules defined!"))

            filter = []

            # loop on rules to get the ruled countries and country groups
            countries_ruled = []
            country_groups_rules = []
            for rule in rules_obj.browse(self.env.cr, self.env.uid, rules):
                if rule.country != None and rule.country.id not in countries_ruled:
                    countries_ruled.append(rule.country.id)
                if rule.region != None and rule.region.id not in country_groups_rules:
                    country_groups_rules.append(rule.region.id)
            _logger.debug("Countries ruled: %s", countries_ruled)
            _logger.debug("Groups of countries ruled: %s", country_groups_rules)

            # check country
            if picking.partner_id.country_id.id in countries_ruled:
                filter.append('|')
                filter.append(['country', '=', picking.partner_id.country_id.id])
                filter.append(['country', '=', False])
            # check for europe
            else:
                if len(countries_ruled) > 0:
                    regions_obj = self.pool.get('res.country.group')
                    regions_id = regions_obj.search(self.env.cr, self.env.uid, [])
                    region_match = False
                    for region in regions_obj.browse(self.env.cr, self.env.uid, regions_id):
                        if picking.partner_id.country_id in region.country_ids:
                            region_match = True
                            filter.append(['region', '=', region.id])
                    # Measns that the country is in ROW
                    if not region_match:
                        filter.append(['region', '=', 'ROW'])

            # Only the rules used for Springer
            filter.append(['used_for_springer', '=', True])

            _logger.debug("Filter: %s", filter)

            rules = rules_obj.search(self.env.cr, self.env.uid, filter, order='priority asc')

            # loop on all rules to find the right one
            for rule in rules_obj.browse(self.env.cr, self.env.uid, rules):
                _logger.debug("Rule: %s - %s", rule.label_number, rule.service)
                # Shipping method (collector/standart/courrier)
                if rule.shipping_method == picking.shipping_method:
                    # Delivery method check between 'initial' and 'subsequent'
                    if rule.delivery_method == 'both' or rule.delivery_method == picking.file_id.job_id.settings_id.delivery_method or picking.file_id.job_id.settings_id.delivery_method == 'both':

                        # PO-Box
                        if picking.po_box == False or picking.po_box == "" or picking.po_box == "None":
                            if rule.po_box == "yes":
                                continue
                        elif picking.po_box != False and picking.po_box != "":
                            if rule.po_box == "no":
                                continue

                        # Postal-permit #
                        if picking.postal_permit_number == False or picking.postal_permit_number == "":
                            if rule.postal_permit == "yes":
                                continue
                        elif picking.postal_permit_number != False and picking.postal_permit_number != "":
                            if rule.postal_permit == "no":
                                continue

                        # ADS
                        if picking.ads == False or picking.ads == "":
                            if rule.ads == "yes":
                                continue
                        elif picking.ads != False and picking.ads != "":
                            if rule.ads == "no":
                                continue

                        # Phone
                        if picking.partner_id.phone == "" or picking.partner_id.phone == False:
                            if rule.phone == "yes":
                                continue
                        elif picking.partner_id.phone != "" and picking.partner_id.phone != False:
                            if rule.phone == "no":
                                continue

                        # Weight
                        if rule.weight_max != 0 and picking.net_picking_weight > rule.weight_max:
                            _logger.debug("Weight too much")
                            continue

                        if picking.net_picking_weight < rule.weight_min:
                            _logger.debug("Weight too low")
                            continue

                        _logger.debug("Rule found: %s", rule.service)

                        # Number of packages
                        if rule.weight_max_package > 0 and rule.weight_max_package < picking.net_picking_weight:
                            picking.logistic_unit_quantity = int((picking.net_picking_weight / rule.weight_max_package) + 1)
                        else:
                            picking.logistic_unit_quantity = 1

                        #  Report
                        picking.shipping_rule = rule
                        picking.logistic_unit_report = rule.label_report
                        break

            # Create the boxes
            if len(picking.boxes) < picking.logistic_unit_quantity:
               i = 1
               while i <= picking.logistic_unit_quantity:
                    self.pool.get('stock.shipping_box').create(self.env.cr, self.env.uid, {
                        'picking_id': picking.id,
                        'state': 'draft',
                    })
                    i += 1

            if not picking.shipping_rule:
                raise osv.except_osv(_("Error"), _("There is no shipping rule that matches this picking list!"))
            
class picking_line(models.Model):
    _inherit = ['stock.move']

    item_number = fields.Char(string="Item Number")
