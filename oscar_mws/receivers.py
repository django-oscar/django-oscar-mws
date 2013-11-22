import logging

from django.utils.translation import ugettext_lazy as _

from .fulfillment import MwsFulfillmentError

logger = logging.getLogger('oscar_mws')


def submit_order_to_mws(order, user, **kwargs):
    if kwargs.get('raw', False):
        return

    # these modules have to be imported here because they rely on loading
    # models from oscar_mws using get_model which are not fully loaded at this
    # point because the receivers module is imported into models.py
    from oscar_mws.fulfillment import gateway
    from oscar_mws.fulfillment.creator import FulfillmentOrderCreator

    try:
        order_creator = FulfillmentOrderCreator()
    except MwsFulfillmentError:
        logger.error(
            "could not create fulfillment order(s) from order {}".format(
                order.number),
            exc_info=1, extra={'order_number': order.number, 'user': user.id})

    submitted_orders = order_creator.create_fulfillment_order(order)
    gateway.submit_fulfillment_orders(submitted_orders)

    failed_orders = [fo.fulfillment_id
                     for fo in submitted_orders
                     if fo.status == fo.SUBMISSION_FAILED]
    if len(failed_orders) > 0:
        for order_id in failed_orders:
            logger.error(
                _("Error submitting orders {} to Amazon").format(
                    ', '.join(failed_orders)))
    else:
        logger.info(
            _("Successfully submitted {0} orders to Amazon").format(
                ', '.join([fo.fulfillment_id for fo in submitted_orders])))
