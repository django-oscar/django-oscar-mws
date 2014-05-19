from lxml import etree
from decimal import Decimal as D
from collections import OrderedDict

from django.test import TestCase
from django.test.utils import override_settings

from oscar.apps.order.models import Line
from oscar.apps.catalogue.models import Product

from oscar_mws.test import factories
from oscar_mws import models as mwsm

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

    def test_deleting_profile_does_not_delete_associated_product(self):
        profile = factories.AmazonProfileFactory()
        self.assertEquals(Product.objects.count(), 1)
        profile.delete()
        self.assertEquals(Product.objects.count(), 1)


class TestFulfillmentOrderLineStatus(TestCase):

    def test_returns_order_status_when_not_shipped(self):
        status = mwsm.FulfillmentOrder.SUBMITTED
        line = mwsm.FulfillmentOrderLine()
        line.fulfillment_order = mwsm.FulfillmentOrder(status=status)
        self.assertEquals(line.status, status)

    def test_returns_shipment_status_when_shipped(self):
        status = 'SHIPPED'
        line = mwsm.FulfillmentOrderLine()
        line.shipment = mwsm.FulfillmentShipment(status=status)
        self.assertEquals(line.status, status)


class TestConvertingAFulfillmentLineToItemDict(TestCase):

    def setUp(self):
        super(TestConvertingAFulfillmentLineToItemDict, self).setUp()
        self.line = mwsm.FulfillmentOrderLine(order_item_id='123', quantity=5)
        self.line.line = Line()

        profile = factories.AmazonProfileFactory(sku='MY-SKU')
        self.line.line.product = profile.product

    def test_returns_correct_data_without_price_or_comment(self):
        expected_kwargs = {
            'SellerSKU': 'MY-SKU',
            'SellerFulfillmentOrderItemId': '123',
            'Quantity': 5
        }
        self.assertItemsEqual(self.line.get_item_kwargs(), expected_kwargs)

    def test_returns_dict_including_price(self):
        self.line.price_incl_tax = D('12.99')
        self.line.price_currency = 'USD'
        expected_kwargs = {
            'SellerSKU': 'MY-SKU',
            'SellerFulfillmentOrderItemId': '123',
            'Quantity': 5,
            'PerUnitDeclaredValue': OrderedDict(
                Value=D('12.99'),
                CurrencyCode='USD',
            )
        }
        self.assertItemsEqual(self.line.get_item_kwargs(), expected_kwargs)

    def test_returns_dict_including_comment(self):
        self.line.comment = 'a comment'
        expected_kwargs = {
            'SellerSKU': 'MY-SKU',
            'SellerFulfillmentOrderItemId': '123',
            'Quantity': 5,
            'DisplayableComment': self.line.comment,
        }
        self.assertItemsEqual(self.line.get_item_kwargs(), expected_kwargs)


class TestMerchantAccount(TestCase):

    def setUp(self):
        super(TestMerchantAccount, self).setUp()
        self.merchant = factories.MerchantAccountFactory()

    def test_returns_empty_list_of_marketplace_ids(self):
        self.assertEquals(self.merchant.marketplace_ids, [])

    def test_returns_list_of_related_market_places(self):
        marketplaces = [
            factories.AmazonMarketplaceFactory(merchant=self.merchant),
            factories.AmazonMarketplaceFactory(merchant=self.merchant)
        ]
        self.merchant.marketplaces.add(marketplaces[0])
        self.merchant.marketplaces.add(marketplaces[1])
        self.assertEquals(self.merchant.marketplace_ids,
                          [m.marketplace_id for m in marketplaces])
