import logging

from dateutil import parser as du_parser

from django.db.models import get_model

from ..connection import get_connection

logger = logging.getLogger('oscar_mws')

Line = get_model('order', 'Line')
ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventType = get_model('order', 'ShippingEventType')

ShipmentPackage = get_model('oscar_mws', 'ShipmentPackage')
FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')
FulfillmentShipment = get_model('oscar_mws', 'FulfillmentShipment')


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

    print [f for f in response.GetFulfillmentOrderResult.FulfillmentShipment]

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
        items = getattr(fshipment.FulfillmentShipmentItem, 'member', [])
        if items:
            item_ids = [i.SellerSKU for i in items]
            fulfillment_lines = Line.objects.filter(
                fulfillment_lines__order_item_id__in=item_ids
            )
            [shipping_event.lines.add(l) for l in fulfillment_lines]

        shipping_note = []
        packages = getattr(fshipment.FulfillmentShipmentPackage, 'member', [])
        for fpackage in packages:
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
