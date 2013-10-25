import mock
import httpretty

from django.test import TestCase
from django.db.models import get_model

from oscar_testsupport.factories import create_order, create_product

from oscar_mws.test import mixins, factories
from oscar_mws.fulfillment.creator import FulfillmentOrderCreator

Country = get_model('address', 'Country')
Basket = get_model('basket', 'Basket')
ShippingAddress = get_model('order', 'ShippingAddress')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')


class TestFulfillmentShipmentCreator(mixins.DataLoaderMixin, TestCase):
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

    @httpretty.activate
    def test_creates_shipments_for_single_address(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/FulfillmentOutboundShipment/2010-10-01',
            body=self.load_data('create_fulfillment_order_response.xml'),
        )
        order = create_order(shipping_address=self.address)
        self.creator.create_fulfillment_order(order)

    @httpretty.activate
    def test_creates_shipments_for_multiple_addresses(self):
        basket = Basket.open.create()
        basket.add_product(create_product())
        basket.add_product(create_product())

        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/FulfillmentOutboundShipment/2010-10-01',
            body=self.load_data('create_fulfillment_order_response.xml'),
        )

        second_address = ShippingAddress.objects.create(
            first_name="test man's friend",
            line1="1 Random Way",
            line4="Spooky Village",
            state="RI",
            postcode="56789",
            country=Country.objects.all()[0],
        )

        order = create_order(basket=basket, shipping_address=self.address)
        order.get_fulfillment_addresses = mock.Mock(
            return_value=[self.address, second_address]
        )

        def get_lines_for_address(address):
            if address == self.address:
                return order.lines.all()[:1]
            return order.lines.all()[1:]
        order.get_lines_for_address = get_lines_for_address

        self.creator.create_fulfillment_order(order)
        self.assertEquals(FulfillmentOrder.objects.count(), 2)


class TestUpdatingFulfillmentOrders(mixins.DataLoaderMixin, TestCase):

    @httpretty.activate
    def test_updates_a_single_order_status(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/',
            responses=[httpretty.Response(
                self.load_data('get_fulfillment_order_response.xml'),
            )],
        )
