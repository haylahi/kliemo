# This code has been written
# by AbAKUS it-solutions PGmbH
# in Belgium, 2015

from openerp import models, fields, api
from openerp.osv import osv
from openerp.tools.translate import _
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

    # -----------------------------------------------------------------------
    # ODOO INHERIT METHODS
    @api.one
    def do_transfer(self):
        cr = self.env.cr
        uid = self.env.user.id
        picking_ids = (self.ids,)
        self.createASNFile()
        super(picking, self).do_transfer()
        _logger.debug('Picking list print report on transfer')
        return self.print_labels()
        #return self.pool['report'].get_action(self.env.cr, self.env.uid, self.id, 'stock_packaging_auto.base_label_report', context=self.env.context) # print the labels

    # -----------------------------------------------------------------------
    # MODEL METHODS
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

class picking_line(models.Model):
    _inherit = ['stock.move']

    item_number = fields.Char(string="Item Number")
