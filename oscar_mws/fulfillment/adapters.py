from collections import OrderedDict

from django.conf import settings

from ..utils import load_class, convert_camel_case

MWS_DEFAULT_SHIPPING_SPEED = getattr(settings, 'MWS_DEFAULT_SHIPPING_SPEED')


class BaseAdapter(object):
    REQUIRED_FIELDS = []
    OPTIONAL_FIELDS = []

    def get_required_fields(self, **kwargs):
        required_fields = OrderedDict()
        for fname in self.REQUIRED_FIELDS:
            method_name = "get_{0}".format(convert_camel_case(fname))
            required_fields[fname] = getattr(self, method_name)(**kwargs)
        return required_fields

    def get_optional_fields(self, **kwargs):
        optional_fields = OrderedDict()
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
    ]
    OPTIONAL_FIELDS = [
        'DisplayableComment',
        'FulfillmentNetworkSKU',
        'OrderItemDisposition',
        'PerUnitDeclaredValue',
    ]

    def __init__(self, line):
        super(OrderLineAdapter, self).__init__()
        self.line = line

    def get_seller_sku(self, **kwargs):
        return self.line.product.amazon_profile.sku

    def get_seller_fulfillment_order_item_id(self, **kwargs):
        return self.line.partner_line_reference or self.get_seller_sku()

    def get_quantity(self, **kwargs):
        return self.line.quantity

    def get_per_unit_declared_value(self, **kwargs):
        if not self.line.unit_price_incl_tax or not self.line.quantity:
            return None

        # The unit price is not mandatory on the line model which means we
        # can't be sure that we have a unit price here. Therefore, we are
        # falling back to calculating an estimated price per unit from its
        # quantity and line price.
        unit_price = self.line.unit_price_incl_tax
        if not unit_price:
            unit_price = self.line.line_price_incl_tax / self.line.quantity
        return OrderedDict(
            CurrencyCode=settings.OSCAR_DEFAULT_CURRENCY,
            Value=unicode(unit_price),
        )

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

    def __init__(self, order):
        super(OrderAdapter, self).__init__()
        self.line_adapter_class = get_order_line_adapter()
        # We store the line adapter instances in this dictionary to avoid
        # re-initialising it several times.
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

    def get_destination_address(self, address, **kwargs):
        return address

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
            adapter = self.line_adapter_class(line=line)
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
            lines = self.order.lines.filter(
                product__amazon_profile__isnull=False)

        return [self.get_line_adapter(l) for l in lines]

    def get_fields(self, address=None, **kwargs):
        if address is None:
            address = self.order.shipping_address

        order_fields = {}
        order_fields.update(
            self.get_required_fields(address=address, **kwargs)
        )
        order_fields.update(
            self.get_optional_fields(address=address, **kwargs)
        )
        return order_fields


def get_order_adapter():
    adapter_class = OrderAdapter
    custom_adapter = getattr(settings, 'MWS_ORDER_ADAPTER', None)
    if custom_adapter:
        adapter_class = load_class(custom_adapter)
    return adapter_class


def get_order_line_adapter():
    adapter_class = OrderLineAdapter
    custom_adapter = getattr(settings, 'MWS_ORDER_LINE_ADAPTER', None)
    if custom_adapter:
        adapter_class = load_class(custom_adapter)
    return adapter_class
