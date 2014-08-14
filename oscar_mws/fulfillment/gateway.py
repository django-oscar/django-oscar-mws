import logging

from collections import defaultdict
from dateutil import parser as du_parser

from django.db.models import get_model
from django.core.exceptions import ObjectDoesNotExist

from oscar.core.loading import get_class

from ..api import MWSObject, MWSError
from ..signals import mws_fulfillment_created
from ..connection import get_merchant_connection

logger = logging.getLogger('oscar_mws')

Partner = get_model('partner', 'Partner')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')

Line = get_model('order', 'Line')
ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')
ShippingEventQuantity = get_model('order', 'ShippingEventQuantity')
EventHandler = get_class('order.processing', 'EventHandler')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentOrderLine = get_model('oscar_mws', 'FulfillmentOrderLine')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')


def _update_shipment(shipment_data, fulfillment_order):
    """
    Updates the fulfillment order *fulfillment_order* with the shipment details
    received from MWS in *shipment_data*. It is a dictionary representation of
    the response received from MWS including details about shipments, packages
    and processing data.
    The data is stored in :class:`FulfillmentShipment
    <oscar_mws.models.FulfillmentShipment>` and :class:`ShipmentPackage
    <oscar_mws.models.ShipmentPackage` instances that are either created or
    updated. If a shipment already exists, it is only handled if it's status
    hasn't changed. For completed shipments, the shipping event as well as
    tracking numbers are stored as shipping events provided by Oscar.

    :param shipment_data: shipment data response from MWS
    :param FulfillmentOrder fulfillment_order: the fulfillment order instance
        that the shipment data should be associated with.
    """
    try:
        shipment = FulfillmentShipment.objects.get(
            shipment_id=shipment_data.AmazonShipmentId
        )
    except FulfillmentShipment.DoesNotExist:
        shipment = FulfillmentShipment.objects.create(
            shipment_id=shipment_data.AmazonShipmentId,
            order=fulfillment_order.order,
        )

    has_status_changed = bool(
        shipment.status != shipment_data.FulfillmentShipmentStatus
    )

    shipment.fulfillment_center_id = shipment_data.FulfillmentCenterId
    shipment.status = shipment_data.FulfillmentShipmentStatus

    if shipment_data.EstimatedArrivalDateTime:
        shipment.date_estimated_arrival = du_parser.parse(
            shipment_data.EstimatedArrivalDateTime
        )

    if shipment_data.ShippingDateTime:
        shipment.date_shipped = du_parser.parse(
            shipment_data.ShippingDateTime
        )
    shipment.save()

    if not has_status_changed:
        logger.info(
            'status for fulfillment shipment unchanged, '
            'no shipping event created', extra={
                'fulfillment_id': fulfillment_order.fulfillment_id,
                'shipment_id': shipment.shipment_id})
        return

    event_type, __ = ShippingEventType.objects.get_or_create(
        name=shipment_data.FulfillmentShipmentStatus
    )

    shipping_note = []
    packages = shipment_data.get('FulfillmentShipmentPackage') or MWSObject()
    for fpackage in packages.get_list('member'):
        ShipmentPackage.objects.get_or_create(
            package_number=fpackage.PackageNumber,
            tracking_number=getattr(fpackage, 'TrackingNumber', None),
            carrier_code=fpackage.CarrierCode,
            fulfillment_shipment=shipment,
        )
        shipping_note.append(
            '* Shipped package via {0} with tracking number {1}'.format(
                fpackage.CarrierCode,
                getattr(fpackage, 'TrackingNumber', None),
            )
        )

    event_handler = EventHandler()

    items = shipment_data.get('FulfillmentShipmentItem') or MWSObject()
    for item in items.get_list('member'):
        fulfillment_lines = FulfillmentOrderLine.objects.filter(
            fulfillment_order=fulfillment_order,
            order_item_id=item.SellerFulfillmentOrderItemId)

        shipping_lines = []
        shipping_quantities = []
        quantity = int(item.Quantity)
        for fline in fulfillment_lines:
            if quantity <= 0:
                break
            if quantity >= fline.quantity:
                shipped_quantity = fline.quantity
            else:
                shipped_quantity = quantity
            shipping_lines.append(fline.line)
            shipping_quantities.append(shipped_quantity)

            quantity = quantity - shipped_quantity
            fline.shipment = shipment
            try:
                fline.package = shipment.packages.get(
                    package_number=item.PackageNumber)
            except ShipmentPackage.DoesNotExist:
                pass
            fline.save()

        if shipping_note:
            reference = '\n'.join(shipping_note)
        else:
            reference = None

        event_handler.validate_shipping_event(
            order=fulfillment_order.order, event_type=event_type,
            lines=shipping_lines, line_quantities=shipping_quantities,
            reference=reference)
        event = event_handler.create_shipping_event(
            order=fulfillment_order.order, event_type=event_type,
            lines=shipping_lines, line_quantities=shipping_quantities,
            reference=reference)
        shipment.shipment_events.add(event)


def submit_fulfillment_orders(orders):
    """
    Submits a list of :class:`FulfillmentOrder
    <oscar_mws.models.FulfillmentOrder>` objects to Amazon requesting
    fulfillment. Each fulfillment order hast to be submitted as a separate API
    request and is therefore handled separately. The status of each fulfillment
    order reflects whether the submission was successful or failed.

    :param list orders: a list of fulfillment orders
    """
    for order in orders:
        submit_fulfillment_order(order)


def submit_fulfillment_order(fulfillment_order):
    """
    Submits the fulfillment order *fulfillment_order* to MWS requesting
    the fulfillment by Amazon. If the submission is succesful, the status of
    the :class:`FulfillmentOrder <oscar_mws.models.FulfillmentOrder>` is
    set to ``SUBMITTED``. Otherwise, the status is changed to
    ``SUBMISSION_FAILED``.

    :param FulfillmentOrder fulfillment_order: A fulfillment order that should
        be fulfilled by Amazon and has a status of ``SUBMISSION_FAILED`` or
        ``UNSUBMITTED`` (not enforced).
    """
    seller_id = fulfillment_order.merchant.seller_id
    outbound_api = get_merchant_connection(seller_id, 'outbound')

    try:
        outbound_api.create_fulfillment_order(
            **fulfillment_order.get_order_kwargs())
    except MWSError:
        logger.error(
            "submitting order {} failed".format(
                fulfillment_order.fulfillment_id), exc_info=1,
            extra={'seller_id': seller_id,
                   'fulfillment_id': fulfillment_order.fulfillment_id,
                   'order_id': fulfillment_order.order.number})
        fulfillment_order.status = fulfillment_order.SUBMISSION_FAILED
    else:
        fulfillment_order.status = fulfillment_order.SUBMITTED
        mws_fulfillment_created.send(
            sender=outbound_api, fulfillment_order=fulfillment_order)
    fulfillment_order.save()


def update_fulfillment_order(fulfillment_order):
    """
    Update the provided *fulfillment_order* with the latest details from MWS.
    Details for the given *fulfillment_order* are requested from MWS, parsed
    and stored in the database.
    It creates/updates ``FulfillmentOrder``, ``FulfillmentShipment`` and
    ``FulfillmentShipmentPackage`` as well as affected ``FulfillmentOrderLine``
    items. As a side-effect, a ``ShippingEvent`` is created for every shipment
    item received from MWS that changes the status of the corresponding model.

    :param FulfillmentOrder fulfillment_order: A fulfillment order has been
        submitted to Amazon.
    """
    outbound_api = get_merchant_connection(
        fulfillment_order.merchant.seller_id, 'outbound')
    try:
        response = outbound_api.get_fulfillment_order(
            order_id=fulfillment_order.fulfillment_id,
        ).parsed
    except MWSError:
        logger.error(
            "updating fulfillment order failed", exc_info=1,
            extra={'fulfillment_id': fulfillment_order.fulfillment_id})
        raise

    forder = response.FulfillmentOrder
    fulfillment_order.status = forder.FulfillmentOrderStatus
    fulfillment_order.save()

    shipments = response.get('FulfillmentShipment') or MWSObject()
    for fshipment in shipments.get_list('member'):
        _update_shipment(fshipment, fulfillment_order)
    return fulfillment_order


def update_fulfillment_orders(fulfillment_orders):
    processed_orders = []
    for order in fulfillment_orders:
        processed_orders.append(update_fulfillment_order(order))
    return processed_orders


def get_all_fulfillment_orders(merchant, query_datetime=None):
    """
    Requests a list of all fulfillment orders available on MWS and creates or
    updates the :class:`FulfillmentOrder <oscar_mws.models.FulfillmentOrder>`
    corresponding to it.

    :rtype list: a list of fulfillment orders added or updated from MWS.
    """
    kwargs = {}
    if query_datetime:
        kwargs['QueryStartDateTime'] = query_datetime.isoformat()

    try:
        response = get_merchant_connection(
            merchant.seller_id
        ).list_all_fulfillment_orders(**kwargs)
    except MWSError:
        logger.error("requesting all fulfillment orders failed", exc_info=1,
                     extra={'seller_id': merchant.seller_id})
        raise

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


def update_inventory(products):
    """
    Update the available inventory for the *products* as available on MWS for
    fulfillment by Amazon. Products that are passed in but don't have a
    merchant account associated with them and/or no :class:`AmazonProfile
    <oscar_mws.models.AmazonProfile>`. For all products that are handled on
    Amazon, the available inventory is retrieved and stored in the stock record
    associated with the combination of :class:`AmazonProfile
    <oscar_mws.models.AmazonProfile>` and :class:`MerchantAccount
    <oscar_mws.models.MerchantAccount>`.

    :param list products: A list of product models.

    :raises MWSError: if an error occurs when communicating with MWS
    """
    product_values = Product.objects.filter(
        id__in=[p.id for p in products],
    ).values_list(
        'amazon_profile__sku',
        'amazon_profile__marketplaces__merchant__seller_id'
    )
    submit_products = defaultdict(set)
    for sku, seller_id in product_values:
        if seller_id is None:
            logger.warning(
                'Product with SKU {} has no seller account'.format(sku))
            continue
        submit_products[seller_id].add(sku)

    for seller_id, skus in submit_products.iteritems():
        inventory_api = get_merchant_connection(seller_id, 'inventory')

        try:
            response = inventory_api.list_inventory_supply(skus=skus).parsed
        except MWSError:
            logger.error(
                'MWS responsed with an error', exc_info=1, extra={
                    'seller_id': seller_id, 'skus': skus})
            raise

        for inventory in response.InventorySupplyList.get_list('member'):
            try:
                stockrecord = StockRecord.objects.get(
                    product__amazon_profile__sku=inventory.SellerSKU,
                    partner__amazon_merchant__seller_id=seller_id)
            except StockRecord.DoesNotExist:
                # It seems that there's no stock record available for the
                # product that is linked to the merchant account. Let's try
                # and create a new stockrecord for this product and merchant's
                # partner. If that fails, we are out of options and just
                # continue with the next one
                try:
                    stockrecord = StockRecord.objects.create(
                        product=Product.objects.get(
                            amazon_profile__sku=inventory.SellerSKU),
                        partner=Partner.objects.get(
                            amazon_merchant__seller_id=seller_id),
                    )
                except ObjectDoesNotExist:
                    logger.error(
                        "no stockrecord and partner found for given product "
                        "and merchant", extra={
                            'seller_sku': inventory.SellerSKU,
                            'seller_id': seller_id})
                    continue
            try:
                quantity = int(inventory.InStockSupplyQuantity)
            except (ValueError, TypeError):
                logger.error(
                    "could not convert '{}' to integer for stock "
                    "record".format(inventory.InStockSupplyQuantity),
                    exc_info=1,
                    extra={'seller_id': seller_id, 'sku': inventory.SellerSKU,
                           'response': response,
                           'value': inventory.InStockSupplyQuantity})
            else:
                stockrecord.set_amazon_supply_quantity(quantity, commit=False)

            stockrecord.save()
