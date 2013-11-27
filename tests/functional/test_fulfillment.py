import httpretty

from dateutil.parser import parse as du_parse

from django.test import TestCase
from django.db.models import get_model

from oscar.test.factories import create_order
from oscar.apps.partner.models import StockRecord

from oscar_mws import mixins as mws_mixins
from oscar_mws.test import mixins, factories
from oscar_mws.fulfillment.creator import FulfillmentOrderCreator
from oscar_mws.fulfillment.gateway import (
    update_fulfillment_order, update_inventory)

ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')
FulfillmentOrderLine = get_model('oscar_mws', 'FulfillmentOrderLine')


class TestCreateFulfillmentOrder(mixins.DataLoaderMixin, TestCase):

    @httpretty.activate
    def test_creates_shipments_for_single_address(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/FulfillmentOutboundShipment/2010-10-01',
            body=self.load_data('create_fulfillment_order_response.xml'),
        )


class TestUpdatingFulfillmentOrders(mixins.DataLoaderMixin, TestCase):

    def setUp(self):
        super(TestUpdatingFulfillmentOrders, self).setUp()
        self.merchant = factories.MerchantAccountFactory()

        self.order = factories.OrderFactory()
        factories.OrderLineFactory(
            order=self.order, product__amazon_profile__sku='SOME-SELLER-SKU')

        creator = FulfillmentOrderCreator()
        self.fulfillment_order = creator.create_fulfillment_order(
            self.order)[0]

    @httpretty.activate
    def test_updates_a_single_order_status(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://mws.amazonservices.com/FulfillmentOutboundShipment/2010-10-01',
            responses=[httpretty.Response(
                self.load_data('get_fulfillment_order_response.xml'),
            )],
        )
        order = update_fulfillment_order(self.fulfillment_order)
        self.assertEquals(order.status, order.COMPLETE)

        shipments = FulfillmentShipment.objects.all()
        self.assertEquals(len(shipments), 1)

        self.assertEquals(shipments[0].status, 'SHIPPED')
        self.assertEquals(shipments[0].shipment_events.count(), 1)

        event = shipments[0].shipment_events.all()[0]
        self.assertEquals(event.event_type.name, 'SHIPPED')
        self.assertSequenceEqual(
            list(event.lines.all()), list(self.order.lines.all()))
        self.assertEquals(
            event.notes,
            "* Shipped package via Magic Parcels with tracking number MPT_1234"
        )

        self.assertEquals(shipments[0].packages.count(), 1)
        package = shipments[0].packages.all()[0]
        self.assertEquals(package.package_number, 2341234)
        self.assertEquals(package.carrier_code, 'Magic Parcels')
        self.assertEquals(package.tracking_number, 'MPT_1234')

    @httpretty.activate
    def test_updates_an_order_without_shipment_info(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://mws.amazonservices.com/FulfillmentOutboundShipment/2010-10-01',
            responses=[httpretty.Response(
                self.load_data(
                    'get_fulfillment_order_response_without_shipments.xml'))],
        )
        order = update_fulfillment_order(self.fulfillment_order)
        self.assertEquals(order.status, order.PLANNING)
        self.assertEquals(FulfillmentShipment.objects.count(), 0)


class TestGetFulfillmentOrder(mixins.DataLoaderMixin, TestCase):

    @httpretty.activate
    def test_parses_the_response_correctly(self):
        xml_data = self.load_data('get_fulfillment_order_response.xml')
        httpretty.register_uri(
            httpretty.GET,
            'https://mws.amazonservices.com/FulfillmentOutboundShipment/2010-10-01',
            body=xml_data,
        )

        basket = factories.BasketFactory()
        basket.add_product(factories.ProductFactory())
        order = create_order(basket=basket)

        update_fulfillment_order(
            factories.FulfillmentOrderFactory(order=order)
        )

        fulfillment_order = FulfillmentOrder.objects.all()[0]
        self.assertEquals(FulfillmentOrder.objects.count(), 1)
        self.assertEquals(fulfillment_order.status, 'COMPLETE')

        shipments = FulfillmentShipment.objects.all()
        self.assertEquals(len(shipments), 1)

        expected = {
            'Dkw.3ko298': {
                'shipment_id': 'Dkw.3ko298',
                'status': 'SHIPPED',
                'fulfillment_center_id': 'FCID01',
                'date_shipped': du_parse('2013-10-29T00:50:03Z'),
                'date_estimated_arrival': du_parse('2013-10-30T23:59:59Z'),
            },
        }
        for shipment in shipments:
            for attr, value in expected[shipment.shipment_id].iteritems():
                self.assertEquals(getattr(shipment, attr), value)

        packages = ShipmentPackage.objects.all()
        self.assertEquals(len(packages), 1)

        self.assertEquals(packages[0].tracking_number, 'MPT_1234')
        self.assertEquals(packages[0].carrier_code, 'Magic Parcels')

        shipping_events = ShippingEvent.objects.all()
        self.assertEquals(len(shipping_events), 1)

        self.assertItemsEqual(
            [s.notes for s in shipping_events],
            ['* Shipped package via Magic Parcels with tracking number '
             'MPT_1234']
        )


class TestUpdateInventory(mixins.DataLoaderMixin, TestCase):

    def setUp(self):
        super(TestUpdateInventory, self).setUp()
        self.original_bases = StockRecord.__bases__
        if not mws_mixins.AmazonStockTrackingMixin in StockRecord.__bases__:
            StockRecord.__bases__ += (mws_mixins.AmazonStockTrackingMixin,)

        marketplace = factories.AmazonMarketplaceFactory()
        product = factories.ProductFactory(
            stockrecord__partner=marketplace.merchant.partner,
            amazon_profile__sku='SKU_12345')
        self.profile = product.amazon_profile
        self.profile.marketplaces.add(marketplace)

        self.assertEquals(self.profile.product.stockrecords.count(), 1)
        self.stockrecord = self.profile.product.stockrecords.all()[0]
        self.assertFalse(self.stockrecord.num_in_stock)
        self.assertFalse(self.stockrecord.num_allocated)

    def tearDown(self):
        super(TestUpdateInventory, self).tearDown()
        StockRecord.__bases__ = self.original_bases

    @httpretty.activate
    def test_with_no_stock_on_stock_record(self):
        xml_data = self.load_data('list_inventory_supply_response.xml')
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/FulfillmentInventory/2010-10-01',
            body=xml_data)

        update_inventory([self.profile.product])

        stockrecord = StockRecord.objects.get(id=self.stockrecord.id)
        self.assertEquals(stockrecord.num_in_stock, 3)
        self.assertEquals(stockrecord.num_allocated, 0)

    @httpretty.activate
    def test_with_invalid_stock_value_in_response(self):
        xml_data = self.load_data('list_inventory_supply_response.xml')
        xml_data = xml_data.replace(
            "<InStockSupplyQuantity>3</InStockSupplyQuantity>",
            "<InStockSupplyQuantity>INVALID</InStockSupplyQuantity>")
        print xml_data
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/FulfillmentInventory/2010-10-01',
            body=xml_data)

        update_inventory([self.profile.product])

        stockrecord = StockRecord.objects.get(id=self.stockrecord.id)
        self.assertFalse(stockrecord.num_in_stock)
        self.assertFalse(stockrecord.num_allocated)
