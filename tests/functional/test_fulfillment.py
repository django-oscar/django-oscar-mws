import httpretty

from dateutil.parser import parse as du_parse

from django.test import TestCase
from django.db.models import get_model

from oscar_testsupport.factories import create_order

from oscar_mws.test import mixins, factories

from oscar_mws.fulfillment.gateway import update_fulfillment_order

ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')


class TestGetFulfillmentOrder(mixins.DataLoaderMixin, TestCase):

    @httpretty.activate
    def test_parses_the_response_correctly(self):
        xml_data = self.load_data('get_fulfillment_order_response.xml')
        httpretty.register_uri(
            httpretty.GET,
            'https://mws.amazonservices.com/FulfillmentOutboundShipment/2010-10-01',
            body=xml_data,
        )

        order = create_order()

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
            ['* Shipped package via Magic Parcels with tracking number MPT_1234']
        )
