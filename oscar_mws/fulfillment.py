import logging

from dateutil import parser as du_parser

from django.conf import settings
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from .utils import convert_camel_case
from .connection import get_connection

logger = logging.getLogger('oscar_mws')

Line = get_model('order', 'Line')
ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')


SHIPPING_STANDARD = 'Standard'
SHIPPING_EXPEDITED = 'Expedited'
SHIPPING_PRIORITY = 'Priority'

SHIPPING_SPEED_CATEGORIES = (
    (SHIPPING_STANDARD, _("Standard")),
    (SHIPPING_EXPEDITED, _("Expedited")),
    (SHIPPING_PRIORITY, _("Priority")),
)

METHOD_CONSUMER = 'Consumer'
METHOD_REMOVAL = 'Removal'

FULFILLMENT_METHODS = (
    (METHOD_CONSUMER, _("Consumer")),
    (METHOD_REMOVAL, _("Removal")),
)

FILL_OR_KILL = 'FillOrKill'
FILL_ALL = 'FillAll'
FILL_ALL_AVAILABLE = 'FillAllAvailable'


class BaseAdapter(object):
    REQUIRED_FIELDS = []
    OPTIONAL_FIELDS = []

    def get_required_fields(self, **kwargs):
        required_fields = {}
        for fname in self.REQUIRED_FIELDS:
            method_name = "get_{0}".format(convert_camel_case(fname))
            required_fields[fname] = getattr(self, method_name)(**kwargs)
        return required_fields

    def get_optional_fields(self, **kwargs):
        optional_fields = {}
        for fname in self.OPTIONAL_FIELDS:
            method_name = "get_{0}".format(convert_camel_case(fname))
            value = getattr(self, method_name)(**kwargs)
            if value:
                optional_fields[fname] = value
        return optional_fields

    def get_fields(self, **kwargs):
        fields = self.get_required_fields(**kwargs)
        fields.update(self.get_optional_fields(**kwargs))
        return fields


class OrderLineAdapter(BaseAdapter):
    REQUIRED_FIELDS = [
        'SellerSKU',
        'SellerFulfillmentOrderItemId',
        'Quantity',
        'PerUnitDeclaredValue',
    ]
    OPTIONAL_FIELDS = [
        'DisplayableComment',
        'FulfillmentNetworkSKU',
        'OrderItemDisposition',
    ]

    def __init__(self, line, merchant_id, marketplace=None):
        self.merchant_id = merchant_id
        self.marketplace = marketplace

        self.line = line

    def get_seller_sku(self, **kwargs):
        return self.line.partner_sku

    def get_seller_fulfillment_order_item_id(self, **kwargs):
        return self.line.partner_line_reference or self.line.partner_sku

    def get_quantity(self, **kwargs):
        return self.line.quantity

    def get_per_unit_declared_value(self, **kwargs):
        return {
            'CurrencyCode': settings.OSCAR_DEFAULT_CURRENCY,
            'Value': self.line.unit_price_incl_tax,
        }

    def get_displayable_comment(self, **kwargs):
        return None

    def get_fulfillment_network_sku(self, **kwargs):
        return None

    def get_order_item_disposition(self, **kwargs):
        return None


class OrderAdapter(BaseAdapter):
    REQUIRED_FIELDS = [
        'SellerFulfillmentOrderId',
        'DisplayableOrderId',
        'DisplayableOrderDateTime',
        'DestinationAddress',
    ]
    OPTIONAL_FIELDS = [
        'NotificationEmailList',
        'DisplayableOrderComment',
    ]

    line_adapter_class = getattr(
        settings,
        'MWS_ORDER_LINE_ADAPTER',
        OrderLineAdapter
    )

    def __init__(self, order, merchant_id, marketplace=None):
        self.merchant_id = merchant_id
        self.marketplace = marketplace

        self.order = order

        self.addresses = self.get_fulfillment_addresses()
        print self.addresses
        self.has_mutliple_destinations = bool(len(self.addresses) > 1)

        self._lines = {}
        for address in self.addresses:
            self._lines[address.id] = self.get_lines(address)
        print self._lines

    def get_suffix(self, address, **kwargs):
        return "{0:03d}".format(self.addresses.index(address) + 1)

    def get_fulfillment_addresses(self):
        try:
            addresses = self.order.get_fulfillment_addresses()
        except AttributeError:
            addresses = [self.order.shipping_address]
        return addresses

    def get_seller_fulfillment_order_id(self, address, **kwargs):
        if self.has_mutliple_destinations:
            return "{0}-{1}".format(
                self.order.number,
                self.get_suffix(address, **kwargs),
            )
        return self.order.number

    def get_displayable_order_id(self, address, **kwargs):
        return self.get_seller_fulfillment_order_id(address, **kwargs)

    def get_displayable_order_date_time(self, address, **kwargs):
        return self.order.date_placed.isoformat(),

    def get_displayable_order_comment(self, address, **kwargs):
        try:
            comment = self.order.get_comment()
        except AttributeError:
            comment = None
        return comment

    def get_destination_address(self, address, **kwargs):
        return {
            'Name': address.name(),
            'Line1': address.line1,
            'Line2': address.line2,
            'line3': address.line3,
            'City': address.city,
            'CountryCode': address.country.iso_3166_1_a2,
            'StateOrProvinceCode': address.state,
            'PostalCode': address.postcode,
        }

    def get_notification_email_list(self, address, **kwargs):
        if not self.order.email:
            return None
        return [self.order.email]

    def get_lines(self, address, **kwargs):
        try:
            lines = self.order.get_lines_for_address(address, **kwargs)
        except AttributeError:
            lines = self.order.lines.all()

        adapted_lines = []
        for line in lines:
            adapted_lines.append(
                self.line_adapter_class(line, merchant_id=self.merchant_id)
            )
        return adapted_lines

    def get_fields(self, address=None, **kwargs):
        if address is None:
            address = self.order.shipping_address

        items = []
        for line in self._lines[address.id]:
            items.append(line.get_fields())

        order_fields = {
            'Items': items,
        }
        order_fields.update(
            self.get_required_fields(address=address, **kwargs)
        )
        order_fields.update(
            self.get_optional_fields(address=address, **kwargs)
        )
        return order_fields


class OutboundShipmentCreator(object):
    order_adapter_class = getattr(
        settings,
        'MWS_ORDER_ADAPTER',
        OrderAdapter
    )

    def __init__(self, merchant_id=None):
        self.merchant_id = merchant_id or getattr(settings, 'MWS_MERCHANT_ID')
        self.mws_connection = get_connection()

    def get_order_adapter(self, order):
        return self.order_adapter_class(
            order=order,
            merchant_id=self.merchant_id,
        )

    def create_shipment_from_order(self, order, **kwargs):
        adapter = self.get_order_adapter(order)

        for address in adapter.addresses:
            order_kwargs = adapter.get_fields(address=address)
            order_kwargs

            outbount_shipment, __ = FulfillmentShipment.objects.get_or_create(
                shipment_id=adapter.get_seller_fulfillment_order_id(
                    address
                ),
                order=order,
            )
            #self.mws_connection.create_fulfillment_order(**order_kwargs)


def update_fulfillment_order(fulfillment_order):
    response = get_connection().get_fulfillment_order(
        SellerFulfillmentOrderId=fulfillment_order.fulfillment_id,
    )

    forder = response.GetFulfillmentOrderResult.FulfillmentOrder
    assert forder.SellerFulfillmentOrderId == fulfillment_order.fulfillment_id

    reported_date = du_parser.parse(forder.StatusUpdatedDateTime)
    if reported_date == fulfillment_order.date_updated:
        return fulfillment_order

    fulfillment_order.status = forder.FulfillmentOrderStatus
    fulfillment_order.save()

    shipment_elem = response.GetFulfillmentOrderResult.FulfillmentShipment
    for fshipment in getattr(shipment_elem, 'member', []):
        try:
            shipment = FulfillmentShipment.objects.get(
                shipment_id=fshipment.AmazonShipmentId
            )
        except FulfillmentShipment.DoesNotExist:
            shipment = FulfillmentShipment.objects.create(
                shipment_id=fshipment.AmazonShipmentId,
                order=fulfillment_order.order,
            )

        has_status_changed = bool(
            shipment.status != fshipment.FulfillmentShipmentStatus
        )

        shipment.fulfillment_center_id = fshipment.FulfillmentCenterId
        shipment.status = fshipment.FulfillmentShipmentStatus

        if fshipment.EstimatedArrivalDateTime:
            shipment.date_estimated_arrival = du_parser.parse(
                fshipment.EstimatedArrivalDateTime
            )

        if fshipment.ShippingDateTime:
            shipment.date_shipped = du_parser.parse(
                fshipment.ShippingDateTime
            )
        shipment.save()

        if not has_status_changed:
            continue

        event_type, __ = ShippingEventType.objects.get_or_create(
            name=fshipment.FulfillmentShipmentStatus
        )
        shipping_event = ShippingEvent.objects.create(
            order=fulfillment_order.order,
            event_type=event_type,

        )
        items = getattr(fshipment.FulfillmentShipmentItem, 'member', [])
        if items:
            item_ids = [i.SellerSKU for i in items]
            fulfillment_lines = Line.objects.filter(
                fulfillment_lines__order_item_id__in=item_ids
            )
            [shipping_event.lines.add(l) for l in fulfillment_lines]

    shipping_note = []
    package_elem = fshipment.FulfillmentShipmentPackage
    for fpackage in getattr(package_elem, 'member', []):
        ShipmentPackage.objects.get_or_create(
            tracking_number=fpackage.TrackingNumber,
            carrier_code=fpackage.CarrierCode,
            fulfillment_shipment=shipment,
        )
        shipping_note.append(
            '* Shipped package via {0} with tracking number {1}'.format(
                fpackage.CarrierCode,
                fpackage.TrackingNumber,
            )
        )
    if shipping_note:
        shipping_event.notes = "\n".join(shipping_note)
        shipping_event.save()
    return fulfillment_order


def update_fulfillment_orders():
    mws_connection = get_connection()
    current_datetime = now()

    #TODO get the timestamp of the last update
