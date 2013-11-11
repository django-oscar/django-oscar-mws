import logging
import itertools

from lxml import etree
from lxml.builder import E, ElementMaker

from django.conf import settings
from django.db.models import get_model

from ..feeds import mappers
from ..utils import load_class

logger = logging.getLogger('oscar_mws')

AmazonProfile = get_model('oscar_mws', 'AmazonProfile')


OP_UPDATE = 'Update'
OP_DELETE = 'Delete'
OP_PARTIAL_UPDATE = 'PartialUpdate'

MSG_TYPE_FULFILLMENT_CENTER = "FulfillmentCenter"
MSG_TYPE_INVENTORY = "Inventory"
MSG_TYPE_LISTINGS = "Listings"
MSG_TYPE_ORDER_ACKNOWLEDGEMENT = "OrderAcknowledgement"
MSG_TYPE_ORDER_ADJUSTMENT = "OrderAdjustment"
MSG_TYPE_ORDER_FULFILLMENT = "OrderFulfillment"
MSG_TYPE_OVERRIDE = "Override"
MSG_TYPE_PRICE = "Price"
MSG_TYPE_PROCESSING_REPORT = "ProcessingReport"
MSG_TYPE_PRODUCT = "Product"
MSG_TYPE_PRODUCT_IMAGE = "ProductImage"
MSG_TYPE_RELATIONSHIP = "Relationship"
MSG_TYPE_SETTLEMENT_REPORT = "SettlementReport"


class BaseFeedWriter(object):
    DOCUMENT_VERSION = '1.01'
    XSI = "http://www.w3.org/2001/XMLSchema-instance"
    NSMAP = {'xsi': XSI}

    def __init__(self, message_type, merchant_id, document_version=None,
                 purge_and_replace=False):
        ENS = ElementMaker(nsmap=self.NSMAP)

        if not purge_and_replace:
            purge_value = 'false'
        else:
            purge_value = 'true'

        self.root = ENS.AmazonEnvelope(
            E.Header(
                E.DocumentVersion(document_version or self.DOCUMENT_VERSION),
                E.MerchantIdentifier(merchant_id),
            ),
            E.MessageType(message_type),
            E.PurgeAndReplace(purge_value),
        )
        attr_name = "{{{0}}}noNamespaceSchemaLocation".format(self.XSI)
        self.root.attrib[attr_name] = "amzn-envelope.xsd"

    def as_string(self, pretty_print=False):
        return etree.tostring(
            self.root,
            pretty_print=pretty_print,
            xml_declaration=True,
            encoding='utf-8'
        )


class ProductFeedWriter(BaseFeedWriter):
    mapper_class = mappers.ProductMapper

    def __init__(self, merchant_id, purge_and_replace=False):
        super(ProductFeedWriter, self).__init__(
            message_type='Product',
            merchant_id=merchant_id,
            purge_and_replace=purge_and_replace,
        )

        mapper = getattr(settings, 'MWS_PRODUCT_MAPPER', None)
        self.mapper_class = load_class(mapper) or self.mapper_class

        self.msg_counter = itertools.count(1)
        self.messages = {}

    def add_product(self, product, operation_type=OP_UPDATE):
        msg_id = self.msg_counter.next()

        msg_elem = E.Message(
            E.MessageID(unicode(msg_id)),
            E.OperationType(operation_type),
            self.mapper_class(product).get_product_xml()
        )
        self.messages[msg_id] = product
        self.root.append(msg_elem)


class InventoryFeedWriter(BaseFeedWriter):
    mapper_class = mappers.InventoryProductMapper

    def __init__(self, merchant_id, purge_and_replace=False, mapper=None):
        super(InventoryFeedWriter, self).__init__(
            message_type='Inventory',
            merchant_id=merchant_id,
            purge_and_replace=purge_and_replace,
        )
        mapper = getattr(settings, 'MWS_INVENTORY_MAPPER', None)
        self.mapper_class = load_class(mapper) or self.mapper_class
        self.msg_counter = itertools.count(1)
        self.messages = {}

    def add_product(self, product, operation_type=OP_UPDATE,
                    fulfillment_center_id=None, fulfillment_by=None):
        msg_id = self.msg_counter.next()

        inventory = E.Inventory(
            self.mapper_class(product).get_value_element('SKU'),
        )
        if fulfillment_center_id:
            inventory.append(E.FulfillmentCenterID(fulfillment_center_id))
            inventory.append(E.Lookup('FulfillmentNetwork'))
        if fulfillment_by:
            inventory.append(E.SwitchFulfillmentTo(fulfillment_by))

        msg_elem = E.Message(
            E.MessageID(unicode(msg_id)),
            E.OperationType(operation_type),
            inventory
        )
        self.messages[msg_id] = product
        self.root.append(msg_elem)
