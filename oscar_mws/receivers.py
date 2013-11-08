import logging

from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger('oscar_mws')


def submit_order_to_mws(order, user, **kwargs):
    if kwargs.get('raw', False):
        return

    # these modules have to be imported here because they rely on loading
    # models from oscar_mws using get_model which are not fully loaded at this
    # point because the receivers module is imported into models.py
    from oscar_mws.fulfillment import gateway
    from oscar_mws.fulfillment.creator import FulfillmentOrderCreator

    order_creator = FulfillmentOrderCreator()
    submitted_orders = order_creator.create_fulfillment_order(order)
    gateway.submit_fulfillment_orders(submitted_orders)

    if not order_creator.errors:
        logger.info(
            _("Successfully submitted {0} orders to Amazon").format(
                len(submitted_orders)
            )
        )
    else:
        for order_id, error in order_creator.errors.iteritems():
            logger.error(
                _("Error submitting order {0} to Amazon: {1}").format(
                    order_id,
                    error
                )
            )
