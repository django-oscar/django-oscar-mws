import mock

from django.test import TestCase
from django.db.models import get_model

from oscar.test.factories import create_order

from oscar_mws.test import factories
from oscar_mws.fulfillment.creator import FulfillmentOrderCreator

Country = get_model('address', 'Country')
Product = get_model('catalogue', 'Product')
ShippingAddress = get_model('order', 'ShippingAddress')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')


class TestFulfillmentShipmentCreator(TestCase):
    fixtures = ['countries']

    def setUp(self):
        super(TestFulfillmentShipmentCreator, self).setUp()
        self.merchant = factories.MerchantAccountFactory()
        self.creator = FulfillmentOrderCreator()
        self.address = ShippingAddress.objects.create(
            first_name='test',
            last_name='man',
            line1="123 Imanginary Ave",
            line4="Funky Town",
            state="CA",
            postcode="56789",
            country=Country.objects.all()[0],
        )
        self.basket = factories.BasketFactory()
        self.basket.add_product(factories.ProductFactory())
        self.basket.add_product(factories.ProductFactory())

    def test_creates_shipments_for_single_address(self):
        order = create_order(basket=self.basket, shipping_address=self.address)
        self.creator.create_fulfillment_order(order)

        mws_orders = FulfillmentOrder.objects.all()
        self.assertEquals(len(mws_orders), 1)
        mws_order = mws_orders[0]
        self.assertEquals(mws_order.status, mws_order.UNSUBMITTED)
        self.assertEquals(mws_order.shipping_address.id, self.address.id)

    def test_creates_shipments_for_multiple_addresses(self):
        second_address = ShippingAddress.objects.create(
            first_name="test man's friend",
            line1="1 Random Way",
            line4="Spooky Village",
            state="RI",
            postcode="56789",
            country=Country.objects.all()[0],
        )

        addresses = [self.address, second_address]
        order = create_order(basket=self.basket, shipping_address=self.address)
        order.get_fulfillment_addresses = mock.Mock(return_value=addresses)

        def get_lines_for_address(address):
            if address == self.address:
                return order.lines.all()[:1]
            return order.lines.all()[1:]
        order.get_lines_for_address = get_lines_for_address

        mws_orders = self.creator.create_fulfillment_order(order)
        self.assertEquals(FulfillmentOrder.objects.count(), 2)

        for mws_order, address in zip(mws_orders, addresses):
            self.assertEquals(mws_order.status, mws_order.UNSUBMITTED)
            self.assertEquals(mws_order.shipping_address.id, address.id)

    def test_ignores_order_lines_without_amazon_profile(self):
        non_mws_product = factories.ProductFactory(amazon_profile=None)
        self.basket.add_product(non_mws_product)
        order = create_order(basket=self.basket, shipping_address=self.address)
        self.creator.create_fulfillment_order(order)

        mws_orders = FulfillmentOrder.objects.all()
        self.assertEquals(len(mws_orders), 1)
        mws_order = mws_orders[0]
        self.assertEquals(mws_order.status, mws_order.UNSUBMITTED)
        self.assertEquals(mws_order.shipping_address.id, self.address.id)
        self.assertItemsEqual(
            [l.product for l in mws_order.lines.all()],
            list(Product.objects.exclude(id=non_mws_product.id)))
