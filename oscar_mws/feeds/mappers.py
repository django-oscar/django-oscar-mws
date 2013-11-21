import re

from lxml import etree
from lxml.builder import E

from datetime import datetime, date

from django.db.models import get_model

AmazonProfile = get_model('oscar_mws', 'AmazonProfile')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')


class BaseProductDataMapper(object):
    product_type = None

    def __init__(self, product):
        self.product = product

    def get_product_data(self, **kwargs):
        pt_elem = getattr(E, self.product_type)()

        attr_values = ProductAttributeValue.objects.filter(
            product=self.product,
            attribute__code__in=self.ATTRIBUTE_MAPPING.keys()
        ).select_related('attribute')

        values = sorted(
            [(self.ATTRIBUTE_MAPPING.get(p.attribute.code), p.value)
             for p in attr_values]
        )
        for name, value in values:
            pt_elem.append(getattr(E, name)(value))

        return getattr(E, self.base_type)(E.ProductType(pt_elem))


class BaseProductMapper(object):

    def __init__(self, product):
        self.product = product

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
        return value

    def get_value_element(self, attr_name):
        pyattr = self.convert_camel_case(attr_name)

        attr_value = self._get_value_from(self, pyattr)
        if attr_value is None:
            attr_value = self._get_value_from(
                self.product.amazon_profile, pyattr)
        if attr_value is None:
            attr_value = self._get_value_from(self.product, pyattr)

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
    PRODUCT_DATA_MAPPERS = {}
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

    def _add_attributes(self, elem, attr_names):
        try:
            self.product.amazon_profile
        except AmazonProfile.DoesNotExist:
            # Assign to the product to make sure it is accessible without
            # having to look it up on the product again
            self.product.amazon_profile = AmazonProfile.objects.create(
                product=self.product)

        for attr in attr_names:
            attr_elem = self.get_value_element(attr)

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

    def get_product_xml(self):
        product_elem = E.Product()
        self._add_attributes(product_elem, self.BASE_ATTRIBUTES)

        desc_elem = etree.SubElement(product_elem, 'DescriptionData')
        self._add_attributes(desc_elem, self.DESCRIPTION_DATA_ATTRIBUTES)

        mapper = self.PRODUCT_DATA_MAPPERS.get(self.product.product_class.slug)
        if mapper:
            sub_tree = mapper(self.product).get_product_data()
            if sub_tree is not None:
                pd_elem = E.ProductData()
                pd_elem.append(sub_tree)
                product_elem.append(pd_elem)
        return product_elem


class InventoryProductMapper(BaseProductMapper):
    pass
