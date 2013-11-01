from django.test import TestCase
from django.test.utils import override_settings

from lxml import etree
from oscar_mws.test import factories


PRODUCT_TYPE_XML = ("<StandardProductID><Type>{}</Type>"
                    "<Value>{}</Value></StandardProductID>")


class TestAmazonProfile(TestCase):

    def test_returns_none_when_upc_too_short(self):
        upc = '123456'
        profile = factories.AmazonProfileFactory(product__upc=upc)
        self.assertEquals(profile.get_standard_product_id(), None)

    def test_returns_none_when_upc_too_long(self):
        upc = '12345678901234567'
        profile = factories.AmazonProfileFactory(product__upc=upc)
        self.assertEquals(profile.get_standard_product_id(), None)

    def test_getting_standard_product_from_upc(self):
        upc = '1234567890'
        profile = factories.AmazonProfileFactory(product__upc=upc)
        spi = profile.get_standard_product_id()
        self.assertEquals(
            etree.tostring(spi),
            PRODUCT_TYPE_XML.format('UPC', upc)
        )

    def test_getting_standard_product_from_asin(self):
        asin = 'FAKE12345'
        profile = factories.AmazonProfileFactory(asin=asin)
        spi = profile.get_standard_product_id()
        self.assertEquals(
            etree.tostring(spi),
            PRODUCT_TYPE_XML.format('ASIN', asin)
        )

    def test_enforcing_stockrecord_partner_sku(self):
        profile = factories.AmazonProfileFactory()
        stockrecord = profile.product.stockrecords.all()[0]
        self.assertEquals(profile.sku, stockrecord.partner_sku)

        profile.sku = 'fake12345'
        profile.save()
        stockrecord = profile.product.stockrecords.all()[0]
        self.assertEquals(profile.sku, stockrecord.partner_sku)

    @override_settings(MWS_ENFORCE_PARTNER_SKU=False)
    def test_enforcing_stockrecord_sku_is_skipped_when_disabled(self):
        profile = factories.AmazonProfileFactory()
        stockrecord = profile.product.stockrecords.all()[0]
        self.assertNotEquals(profile.sku, stockrecord.partner_sku)
