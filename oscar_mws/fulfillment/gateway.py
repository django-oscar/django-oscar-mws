import logging

from collections import defaultdict
from dateutil import parser as du_parser

from django.db.models import get_model

from ..api import MWSObject, MWSError
from ..connection import get_merchant_connection

logger = logging.getLogger('oscar_mws')

Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')

Line = get_model('order', 'Line')
ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')
ShippingEventQuantity = get_model('order', 'ShippingEventQuantity')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')


def update_fulfillment_order(fulfillment_order):
    outbound_api = get_merchant_connection(
        fulfillment_order.merchant.seller_id
    ).outbound
    try:
        response = outbound_api.get_fulfillment_order(
            order_id=fulfillment_order.fulfillment_id,
        ).parsed
    except MWSError as exc:
        logger.error(
            "[{exc.error_code}]: {exc.reason} : {exc.message} (Request ID: "
            "{exc.request_id})".format(exc=exc)
        )
        return

    forder = response.FulfillmentOrder
    #assert response.SellerFulfillmentOrderId == fulfillment_order.fulfillment_id

    reported_date = du_parser.parse(forder.StatusUpdatedDateTime)
    if reported_date == fulfillment_order.date_updated:
        return fulfillment_order

    fulfillment_order.status = forder.FulfillmentOrderStatus
    fulfillment_order.save()

    for fshipment in response.FulfillmentShipment.get_list('member'):
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

        shipping_note = []
        packages = fshipment.get('FulfillmentShipmentPackage', MWSObject())
        for fpackage in packages.get_list('member'):
            ShipmentPackage.objects.get_or_create(
                package_number=fpackage.PackageNumber,
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

        items = fshipment.get('FulfillmentShipmentItem', MWSObject())
        for item in items.get_list('member'):
            fulfillment_lines = Line.objects.filter(
                fulfillment_line__order_item_id=item.SellerSKU
            )
            for fline in fulfillment_lines:
                try:
                    seq = ShippingEventQuantity.objects.get(
                        event=shipping_event,
                        line=fline,
                    )
                except ShippingEventQuantity.DoesNotExist:
                    seq = ShippingEventQuantity(
                        event=shipping_event,
                        line=fline,
                    )
                seq.quantity = int(item.Quantity)
                seq.save()

                fline.shipment = shipment
                try:
                    fline.package = shipment.packages.get(
                        package_number=item.PackageNumber
                    )
                except ShipmentPackage.DoesNotExist:
                    pass
                fline.save()

    return fulfillment_order


def update_fulfillment_orders(fulfillment_orders):
    processed_orders = []
    for order in fulfillment_orders:
        try:
            processed_orders.append(update_fulfillment_order(order))
        except MWSError as exc:
            logger.error(
                "[{exc.error_code}]: {exc.reason} : {exc.message} "
                "(Request ID: {exc.request_id})".format(exc=exc)
            )
    return processed_orders


def get_all_fulfillment_orders(merchant, query_datetime=None):
    kwargs = {}
    if query_datetime:
        kwargs['QueryStartDateTime'] = query_datetime.isoformat()

    try:
        response = get_merchant_connection(
            merchant.seller_id
        ).list_all_fulfillment_orders(**kwargs)
    except MWSError as exc:
        logger.error(
            "[{exc.error_code}]: {exc.reason} : {exc.message} "
            "(Request ID: {exc.request_id})".format(exc=exc)
        )
        return []

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
    product_values = Product.objects.filter(
        id__in=[p.id for p in products],
    ).values_list(
        'stockrecord__partner_sku',
        'amazon_profile__marketplaces__merchant__seller_id'
    )
    submit_products = defaultdict(set)
    for sku, seller_id in product_values:
        if seller_id is None:
            logger.info(
                'Product with SKU {} has no seller account'.format(sku)
            )
            continue
        submit_products[seller_id].add(sku)

    for seller_id, skus in submit_products.iteritems():
        print 'SELLER ID', seller_id
        inventory_api = get_merchant_connection(seller_id).inventory
        response = inventory_api.list_inventory_supply(skus=skus).parsed

        for inventory in response.InventorySupplyList.get_list('member'):
            try:
                stockrecord = StockRecord.objects.get(
                    partner_sku=inventory.SellerSKU
                )
            except StockRecord.DoesNotExist:
                logger.error(
                    "could not find stock record for SKU {}".format(
                        inventory.SellerSKU
                    )
                )
            stockrecord.num_in_stock = inventory.InStockSupplyQuantity
            stockrecord.save()
