from django.conf import settings
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from boto.mws.exception import ResponseError

from .adapters import OrderAdapter
from ..utils import load_class
from ..connection import get_merchant_connection

FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentOrderLine = get_model('oscar_mws', 'FulfillmentOrderLine')


class FulfillmentOrderCreator(object):
    order_adapter_class = OrderAdapter

    def __init__(self, merchant, order_adapter_class=None):
        custom_adapter = getattr(settings, 'MWS_ORDER_ADAPTER', None)
        if custom_adapter:
            self.order_adapter_class = load_class(custom_adapter)

        self.merchant = merchant
        self.mws_connection = get_merchant_connection(merchant.seller_id)

        self.errors = {}

    def get_order_adapter(self, order):
        return self.order_adapter_class(
            order=order,
            merchant_id=self.merchant.seller_id,
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
                    merchant=self.merchant,
                )
            except FulfillmentOrder.DoesNotExist:
                fulfillment_order = FulfillmentOrder(
                    fulfillment_id=fulfillment_id,
                )
                try:
                    self.mws_connection.create_fulfillment_order(
                        **adapter.get_fields(address=address)
                    )
                except ResponseError as exc:
                    self.errors[fulfillment_id] = exc.message
                    continue

                fulfillment_order.order = order
                fulfillment_order.merchant = self.merchant
                fulfillment_order.save()
            else:
                self.errors[fulfillment_id] = _("Order already submitted.")

            fulfillment_orders.append(fulfillment_order)

            for la in adapter.get_lines(address=address):
                FulfillmentOrderLine.objects.get_or_create(
                    line=la.line,
                    fulfillment_order=fulfillment_order,
                    order_item_id=la.get_seller_fulfillment_order_item_id(),
                )

        return fulfillment_orders
