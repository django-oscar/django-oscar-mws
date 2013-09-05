import re
import logging
import itertools

from datetime import datetime, date

from lxml import etree
from lxml.builder import E, ElementMaker

from django.db.models import get_model

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


class BaseProductMapper(object):

    def convert_camel_case(self, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _get_value_from(self, obj, attr):
        """
        Get value from the *obj* for the given attribute name in *attr*. First
        this method attempts to retrieve the value from a ``get_<attr>``
        method then falls back to a simple attribute.
        """
        method_name = 'get_{0}'.format(attr)
        if hasattr(obj, method_name):
            return getattr(obj, method_name)()
        value = getattr(obj, attr, None)
        #TODO this should be limited to only fields that are required in
        # the feed.
        #if not value:
        #    raise AttributeError(
        #        "can't find attribute or function for {0}. Make sure you "
        #        "have either of them defined and try again".format(attr)
        #    )
        return value

    def get_value_element(self, product, attr_name):
        pyattr = self.convert_camel_case(attr_name)

        attr_value = self._get_value_from(product.amazon_profile, pyattr)
        if not attr_value:
            attr_value = self._get_value_from(product, pyattr)
        if not attr_value:
            attr_value = self._get_value_from(self, pyattr)

        # if we still have no value we assume it is optional and
        # we just leave it out of the generated XML.
        if not attr_value:
            return None


        if isinstance(attr_value, etree._Element):
            return attr_value

        if not isinstance(attr_value, basestring):
            attr_value = self.serialise(attr_value)
        elem = etree.Element(attr_name)
        elem.text = attr_value
        return elem


class ProductMapper(BaseProductMapper):
    BASE_ATTRIBUTES = [
        "SKU",
        "StandardProductID",
        "ProductTaxCode",
        "LaunchDate",
        "DiscontinueDate",
        "ReleaseDate",
        "ExternalProductUrl",
        "OffAmazonChannel",
        "OnAmazonChannel",
        "Condition",
        "Rebate",
        "ItemPackageQuantity",
        "NumberOfItems",
    ]
    DESCRIPTION_DATA_ATTRIBUTES = [
        "Title",
        "Brand",
        "Designer",
        "Description",
        "BulletPoint",
        "ItemDimensions",
        "PackageDimensions",
        "PackageWeight",
        "ShippingWeight",
        "MerchantCatalogNumber",
        "MSRP",
        "MaxOrderQuantity",
        "SerialNumberRequired",
        "Prop65",
        "LegalDisclaimer",
        "Manufacturer",
        "MfrPartNumber",
        "SearchTerms",
        "PlatinumKeywords",
        "RecommendedBrowseNode",
        "Memorabilia",
        "Autographed",
        "UsedFor",
        "ItemType",
        "OtherItemAttributes",
        "TargetAudience",
        "SubjectContent",
        "IsGiftWrapAvailable",
        "IsGiftMessageAvailable",
        "IsDiscontinuedByManufacturer",
        "MaxAggregateShipQuantity",
    ]

    def _add_attributes(self, product, elem, attr_names):
        try:
            product.amazon_profile
        except AmazonProfile.DoesNotExist:
            # Assign to the product to make sure it is accessible without
            # having to look it up on the product again
            product.amazon_profile = AmazonProfile.objects.create(
                product=product
            )

        for attr in attr_names:
            attr_elem = self.get_value_element(product, attr)

            if attr_elem is not None:
                elem.append(attr_elem)

    def serialise(self, value):
        """
        Very basic an naive serialiser function for python types to the
        Amazon XML representation.
        """
        if not value:
            return u''
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return unicode(value)

    def get_product_xml(self, product):
        product_elem = E.Product()
        self._add_attributes(product, product_elem, self.BASE_ATTRIBUTES)

        desc_elem = etree.SubElement(product_elem, 'DescriptionData')
        self._add_attributes(
            product,
            desc_elem,
            self.DESCRIPTION_DATA_ATTRIBUTES
        )
        return product_elem


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
    mapper_class = ProductMapper

    def __init__(self, merchant_id, purge_and_replace=False, mapper=None):
        super(ProductFeedWriter, self).__init__(
            message_type='Product',
            merchant_id=merchant_id,
            purge_and_replace=purge_and_replace,
        )

        self.mapper_class = mapper or self.mapper_class
        self.msg_counter = itertools.count(1)
        self.messages = {}

    def add_product(self, product, operation_type=OP_UPDATE):
        msg_id = self.msg_counter.next()

        msg_elem = E.Message(
            E.MessageID(unicode(msg_id)),
            E.OperationType(operation_type),
            self.mapper_class().get_product_xml(product)
        )
        self.messages[msg_id] = product
        self.root.append(msg_elem)

    def validate_xml(self):
        if not self.schema:
            with open('oscar_mws/xsd/amzn-base.xsd') as xsdfh:
                schema_doc = etree.parse(xsdfh)
                self.schema = etree.XMLSchema(schema_doc)
        is_valid = self.schema.validate(self.root)
        if not is_valid:
            logger.debug(
                "product feed XML not valid: {0}".format(self.schema.error.log)
            )


class InventoryFeedWriter(BaseFeedWriter):
    mapper_class = BaseProductMapper

    def __init__(self, merchant_id, purge_and_replace=False, mapper=None):
        super(InventoryFeedWriter, self).__init__(
            message_type='Inventory',
            merchant_id=merchant_id,
            purge_and_replace=purge_and_replace,
        )
        self.msg_counter = itertools.count(1)
        self.messages = {}

    def add_product(self, product, operation_type=OP_UPDATE,
                    fulfillment_center_id=None, fulfillment_by=None):
        msg_id = self.msg_counter.next()

        inventory = E.Inventory(
            self.mapper_class().get_value_element(product, 'SKU'),
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
