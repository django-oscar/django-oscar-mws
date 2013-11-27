from decimal import Decimal as D

from django.conf import settings
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

from . import adapters
from ..utils import load_class
from . import MwsFulfillmentError

MerchantAccount = get_model('oscar_mws', 'MerchantAccount')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentOrderLine = get_model('oscar_mws', 'FulfillmentOrderLine')


class FulfillmentOrderCreator(object):

    def __init__(self):
        self.order_adapter_class = adapters.get_order_adapter()
        self.errors = {}
        try:
            self.find_fulfillment_merchant = load_class(
                getattr(settings, 'MWS_FULFILLMENT_MERCHANT_FINDER', None)
            )
        except ImportError:
            raise ImproperlyConfigured(
                "no fulfillment merchant finder callable configured in "
                "MWS_FULFILLMENT_MERCHANT_FINDER setting. Check your settings "
                "file and try again."
            )

    def get_order_adapter(self, order):
        return self.order_adapter_class(order=order)

    def create_fulfillment_order(self, order, lines=None, **kwargs):
        adapter = self.get_order_adapter(order)

        fulfillment_orders = []
        for address in adapter.addresses:
            fulfillment_id = adapter.get_seller_fulfillment_order_id(address)
            order_kw = adapter.get_fields(address=address)

            try:
                merchant = self.find_fulfillment_merchant(order, address)
            except MwsFulfillmentError:
                merchant = None
            if not merchant:
                self.errors[fulfillment_id] = _(
                    "could not find suitable merchant for fulfillemnt order "
                    "{}". format(fulfillment_id)
                )
                continue

            try:
                fulfillment_order = FulfillmentOrder.objects.get(
                    fulfillment_id=fulfillment_id, order=order,
                    merchant=merchant)
            except FulfillmentOrder.DoesNotExist:
                fulfillment_order = FulfillmentOrder.objects.create(
                    fulfillment_id=fulfillment_id,
                    order=order,
                    merchant=merchant,
                    shipping_address=order_kw.get('DestinationAddress'),
                    shipping_speed=order_kw.get('ShippingSpeedCategory'),
                    comments=order_kw.get('DisplayableOrderComment'),
                )
            else:
                self.errors[fulfillment_id] = _("Order already created.")

            fulfillment_orders.append(fulfillment_order)

            for line_adapter in adapter.get_lines(address=address):
                self.create_fulfillment_line(line_adapter, fulfillment_order)
        return fulfillment_orders

    def create_fulfillment_line(self, line_adapter, fulfillment_order):
        try:
            line = FulfillmentOrderLine.objects.get(
                line=line_adapter.line, fulfillment_order=fulfillment_order)
        except FulfillmentOrderLine.DoesNotExist:
            line = FulfillmentOrderLine(
                line=line_adapter.line, fulfillment_order=fulfillment_order)

        line_kwargs = line_adapter.get_fields()
        line.order_item_id = \
            line_adapter.get_seller_fulfillment_order_item_id()
        line.quantity = line_kwargs.get('Quantity')
        line.comment = line_kwargs.get('DisplayableOrderComment', '')
        price = line_kwargs.get('PerUnitDeclaredValue')
        if price and price.get('Value'):
            line.price_incl_tax = D(price.get('Value'))
            line.price_currency = price.get('Currency')
        line.save()
