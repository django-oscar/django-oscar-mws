from mock import Mock

from django.test import TestCase

from oscar.apps.partner.models import StockRecord

from oscar_mws.test import factories
from oscar_mws.mixins import AmazonStockTrackingMixin


class TestUpdateStockLevels(TestCase):

    def setUp(self):
        self.stock_record = AmazonStockTrackingMixin()
        self.stock_record.save = Mock()
        self.stock_record.num_in_stock = 0
        self.stock_record.num_allocated = 0

    def test_when_both_fields_are_zero(self):
        self.stock_record.set_amazon_supply_quantity('12')
        self.assertEquals(self.stock_record.num_in_stock, 12)
        self.assertEquals(self.stock_record.num_allocated, 0)
        self.stock_record.save.assert_called_once_with()

    def test_when_stock_is_allocated(self):
        self.stock_record.num_in_stock = 10
        self.stock_record.num_allocated = 5
        self.stock_record.set_amazon_supply_quantity('12')
        self.assertEquals(self.stock_record.num_in_stock, 12)
        self.assertEquals(self.stock_record.num_allocated, 0)
        self.stock_record.save.assert_called_once_with()


class TestStockRecord(TestCase):

    def setUp(self):
        super(TestStockRecord, self).setUp()
        self.merchant = factories.MerchantAccountFactory()
        self.original_bases = StockRecord.__bases__
        StockRecord.__bases__ = \
            (AmazonStockTrackingMixin,) + StockRecord.__bases__

    def tearDown(self):
        super(TestStockRecord, self).tearDown()
        StockRecord.__bases__ = self.original_bases

    def test_returns_false_if_it_isnt_mws_stockrecord(self):
        stock_record = StockRecord.objects.create(
            product=factories.ProductFactory(),
            partner=factories.PartnerFactory())
        self.assertFalse(stock_record.is_mws_record)

    def test_returns_true_if_it_is_mws_stockrecord(self):
        self.assertTrue(self.merchant.partner.name.startswith('Amazon'))
        stock_record = StockRecord.objects.create(
            product=factories.ProductFactory(),
            partner=self.merchant.partner)
        self.assertTrue(stock_record.is_mws_record)

    def test_doesnt_change_stock_when_mws_record(self):
        stock_record = StockRecord.objects.create(
            product=factories.ProductFactory(),
            partner=self.merchant.partner)
        stock_record.num_in_stock = 12
        stock_record.num_allocated = 3
        stock_record.consume_allocation(quantity=1)
        self.assertEquals(stock_record.num_in_stock, 12)
        self.assertEquals(stock_record.num_allocated, 3)

    def test_changes_stock_when_it_isnt_mws_record(self):
        stock_record = StockRecord.objects.create(
            product=factories.ProductFactory(),
            partner=factories.PartnerFactory())
        stock_record.num_in_stock = 12
        stock_record.num_allocated = 3
        stock_record.consume_allocation(quantity=2)
        self.assertEquals(stock_record.num_in_stock, 10)
        self.assertEquals(stock_record.num_allocated, 1)
