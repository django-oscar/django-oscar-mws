import logging

from dateutil import parser as du_parser

from django.conf import settings
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from boto.mws.response import ResponseElement
from boto.mws.exception import ResponseError

from .connection import get_connection
from .utils import load_class, convert_camel_case

logger = logging.getLogger('oscar_mws')

Line = get_model('order', 'Line')
ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')
FulfillmentOrderLine = get_model('oscar_mws', 'FulfillmentOrderLine')


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

MWS_DEFAULT_SHIPPING_SPEED = getattr(settings, 'MWS_DEFAULT_SHIPPING_SPEED')


class BaseAdapter(object):
    REQUIRED_FIELDS = []
    OPTIONAL_FIELDS = []

    def __init__(self, merchant_id, marketplace_id=None):
        self.merchant_id = merchant_id
        self.marketplace = marketplace_id

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
        return ResponseElement(name=self.__class__, attrs=fields)


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

    def __init__(self, line, merchant_id, marketplace_id=None):
        super(OrderLineAdapter, self).__init__(merchant_id, marketplace_id)
        self.line = line

    def get_seller_sku(self, **kwargs):
        return self.line.partner_sku

    def get_seller_fulfillment_order_item_id(self, **kwargs):
        return self.line.partner_line_reference or self.line.partner_sku

    def get_quantity(self, **kwargs):
        return self.line.quantity

    def get_per_unit_declared_value(self, **kwargs):
        return ResponseElement(attrs={
            'CurrencyCode': settings.OSCAR_DEFAULT_CURRENCY,
            'Value': str(self.line.unit_price_incl_tax),
        })

    def get_displayable_comment(self, **kwargs):
        return None

    def get_fulfillment_network_sku(self, **kwargs):
        return None

    def get_order_item_disposition(self, **kwargs):
        return None


class OrderAdapter(BaseAdapter):
    REQUIRED_FIELDS = [
        'DisplayableOrderId',
        'DisplayableOrderDateTime',
        'DisplayableOrderComment',
        'DestinationAddress',
        'SellerFulfillmentOrderId',
        'ShippingSpeedCategory',
    ]
    OPTIONAL_FIELDS = [
        'NotificationEmailList',
    ]
    line_adapter_class = OrderLineAdapter

    def __init__(self, order, merchant_id, marketplace_id=None):
        super(OrderAdapter, self).__init__(merchant_id, marketplace_id)
        custom_adapter = getattr(settings, 'MWS_ORDER_LINE_ADAPTER', None)
        if custom_adapter:
            self.line_adapter_class = load_class(custom_adapter)

        self.line_adapters = {}

        self.order = order

        self.addresses = self.get_fulfillment_addresses()
        self.has_mutliple_destinations = bool(len(self.addresses) > 1)

        self._lines = {}
        for address in self.addresses:
            self._lines[address.id] = self.get_lines(address)

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

    def get_line_adapter(self, line):
        try:
            adapter = self.line_adapters[line.id]
        except KeyError:
            adapter = self.line_adapter_class(
                line=line,
                merchant_id=self.merchant_id
            )
            self.line_adapters[line.id] = adapter
        return self.line_adapters[line.id]

    def get_displayable_order_id(self, address, **kwargs):
        return self.get_seller_fulfillment_order_id(address, **kwargs)

    def get_displayable_order_date_time(self, address, **kwargs):
        return self.order.date_placed.isoformat()

    def get_displayable_order_comment(self, address, **kwargs):
        try:
            comment = self.order.get_comment()
        except AttributeError:
            comment = "Thanks for placing an order with us!"
        return comment

    def get_destination_address(self, address, **kwargs):
        return ResponseElement(
            name="DestinationAddress",
            attrs={
                'Name': address.name,
                'Line1': address.line1,
                'Line2': address.line2,
                'line3': address.line3,
                'City': address.city,
                'CountryCode': address.country.iso_3166_1_a2,
                'StateOrProvinceCode': address.state,
                'PostalCode': address.postcode,
            }
        )

    def get_shipping_speed_category(self, **kwargs):
        return MWS_DEFAULT_SHIPPING_SPEED

    def get_notification_email_list(self, address, **kwargs):
        if not self.order.email:
            return None
        return [self.order.email]

    def get_lines(self, address, **kwargs):
        try:
            lines = self.order.get_lines_for_address(address, **kwargs)
        except AttributeError:
            lines = self.order.lines.all()

        return [self.get_line_adapter(l) for l in lines]

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


class FulfillmentOrderCreator(object):
    order_adapter_class = OrderAdapter

    def __init__(self, merchant_id=None, order_adapter_class=None):
        custom_adapter = getattr(settings, 'MWS_ORDER_ADAPTER', None)
        if custom_adapter:
            self.order_adapter_class = load_class(custom_adapter)

        self.merchant_id = merchant_id or getattr(settings, 'MWS_SELLER_ID')
        self.mws_connection = get_connection()

        self.errors = {}

    def get_order_adapter(self, order):
        return self.order_adapter_class(
            order=order,
            merchant_id=self.merchant_id,
        )

    def create_fulfillment_order(self, order, lines=None, **kwargs):
        adapter = self.get_order_adapter(order)

        fulfillment_orders = []
        for address in adapter.addresses:
            fulfillment_id = adapter.get_seller_fulfillment_order_id(address)
            try:
                fulfillment_order = FulfillmentOrder.objects.get(
                    fulfillment_id=fulfillment_id,
                    order=order,
                )
            except FulfillmentOrder.DoesNotExist:
                fulfillment_order = FulfillmentOrder(
                    fulfillment_id=fulfillment_id,
                    order=order,
                )
                try:
                    self.mws_connection.create_fulfillment_order(
                        **adapter.get_fields(address=address)
                    )
                except ResponseError as exc:
                    self.errors[fulfillment_id] = exc.message
                    continue

                fulfillment_order.order = order
                fulfillment_order.save()
            else:
                self.errors[fulfillment_id] = _("Order already submitted.")

            fulfillment_orders.append(fulfillment_order)

            for line_adapter in adapter.get_lines(address=address):
                FulfillmentOrderLine.objects.get_or_create(
                    line=line_adapter.line,
                    fulfillment_order=fulfillment_order,
                    order_item_id=line_adapter.get_seller_fulfillment_order_item_id(),
                )

        return fulfillment_orders


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

    for fshipment in response.GetFulfillmentOrderResult.FulfillmentShipment:
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
        for fpackage in fshipment.FulfillmentShipmentPackage:
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


def update_fulfillment_orders(fulfillment_orders):
    processed_orders = []
    for order in fulfillment_orders:
        processed_orders.append(update_fulfillment_order(order))
    return processed_orders


def get_all_fulfillment_orders(query_datetime=None):
    kwargs = {}
    if query_datetime:
        kwargs['QueryStartDateTime'] = query_datetime.isoformat()

    response = get_connection().list_all_fulfillment_orders(**kwargs)
    print response

    processed_orders = []
    for forder in response.ListAllFulfillmentOrdersResult.FulfillmentOrders:
        fulfillment_order, __ = FulfillmentOrder.objects.get_or_create(
            fulfillment_id=forder.SellerFulfillmentOrderId
        )

        reported_date = du_parser.parse(forder.StatusUpdatedDateTime)
        if reported_date == fulfillment_order.date_updated:
            return fulfillment_order

        fulfillment_order.status = forder.FulfillmentOrderStatus
        fulfillment_order.save()
    return processed_orders
