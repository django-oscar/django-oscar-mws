import re
import itertools

from lxml import etree
from lxml.builder import E, ElementMaker

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

    def convert_camel_case(self, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _get_value_from(self, obj, attr):
        """
        Get value from the *obj* for the given attribute name in *attr*. First
        this method attempts to retrieve the value from a ``get_<attr>``
        method then falls back to a simple attribute. If neither of them is
        available, an ``AttributeError`` is raised.
        """
        method_name = 'get_{0}'.format(attr)
        if hasattr(obj, method_name):
            return getattr(obj, method_name)()
        value = getattr(obj, attr, None)
        if not value:
            raise AttributeError(
                "can't find attribute or function for {0}. Make sure you "
                "have either of them defined and try again".format(attr)
            )
        return value

    def _add_attributes(self, product, elem, attr_names):
        for attr in attr_names:
            pyattr = self.convert_camel_case(attr)

            attr_value = None
            if hasattr(product, 'amazon_profile'):
                attr_value = self._get_value_from(
                    product.amazon_profile,
                    pyattr
                )
            if not attr_value:
                attr_value = self._get_value_from(product, pyattr)
            if not attr_value:
                attr_value = self._get_value_from(self, pyattr)

            etree.SubElement(elem, attr, attr_value)

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


class ProductFeedWriter(object):
    XSI = "http://www.w3.org/2001/XMLSchema-instance"
    NSMAP = {'xsi': XSI}

    mapper_class = BaseProductMapper

    def __init__(self, merchant_id, purge_and_replace=False, mapper=None):
        if mapper:
            self.mapper_class = mapper
        if not purge_and_replace:
            purge_value = 'false'
        else:
            purge_value = 'true'

        ENS = ElementMaker(nsmap=self.NSMAP)
        self.root = ENS.AmazonEnvelope(
            E.Header(
                E.DocumentVersion("1.01"),
                E.MerchantIdentifier(merchant_id),
            ),
            E.MessageType('Product'),
            E.PurgeAndReplace(purge_value),
        )
        attr_name = "{{{0}}}noNamespaceSchemaLocation".format(self.XSI)
        self.root.attrib[attr_name] = "amzn-envelope.xsd"

        self.msg_counter = itertools.count(1)
        self.message = {}

    def add_product(self, product, operation_type=OP_UPDATE):
        msg_id = self.msg_counter.next()
        msg_elem = E.Message(
            E.MessageID(msg_id),
            E.OperationType(operation_type),
            self.mapper_class.get_product_xml(product)
        )
        self.messages[msg_id] = product

    def as_string(self, pretty_print=False):
        return etree.tostring(
            self.root,
            pretty_print=pretty_print,
            xml_declaration=True,
            encoding='iso-8859-1'
        )


#<Header>
#<DocumentVersion>1.01</DocumentVersion>
#<MerchantIdentifier>M_EXAMPLE_123456</MerchantIdentifier>
#</Header>
#<MessageType>Product</MessageType>
#<PurgeAndReplace>false</PurgeAndReplace>
