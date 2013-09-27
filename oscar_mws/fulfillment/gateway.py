import logging

from dateutil import parser as du_parser

from boto.mws.exception import ResponseError

from django.db.models import get_model

from ..connection import get_merchant_connection

logger = logging.getLogger('oscar_mws')

Line = get_model('order', 'Line')
ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')


def update_fulfillment_order(fulfillment_order):
    mws_connection = get_merchant_connection(
        fulfillment_order.merchant.seller_id
    )
    try:
        response = mws_connection.get_fulfillment_order(
            SellerFulfillmentOrderId=fulfillment_order.fulfillment_id,
        )
    except ResponseError as exc:
        logger.error(
            "[{exc.error_code}]: {exc.reason} : {exc.message} (Request ID: "
            "{exc.request_id})".format(exc=exc)
        )
        return

    forder = response.GetFulfillmentOrderResult.FulfillmentOrder
    assert forder.SellerFulfillmentOrderId == fulfillment_order.fulfillment_id

    reported_date = du_parser.parse(forder.StatusUpdatedDateTime)
    if reported_date == fulfillment_order.date_updated:
        return fulfillment_order

    fulfillment_order.status = forder.FulfillmentOrderStatus
    fulfillment_order.save()

    fshipments = getattr(
        response.GetFulfillmentOrderResult.FulfillmentShipment,
        'member',
        []
    )
    for fshipment in fshipments:
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
        packages = getattr(fshipment.FulfillmentShipmentPackage, 'member', [])
        for fpackage in packages:
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

        for item in getattr(fshipment.FulfillmentShipmentItem, 'member', []):
            fulfillment_lines = Line.objects.filter(
                fulfillment_line__order_item_id=item.SellerSKU
            )
            for fline in fulfillment_lines:
                shipping_event.lines.add(fline)
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
        except ResponseError as exc:
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
    except ResponseError as exc:
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
