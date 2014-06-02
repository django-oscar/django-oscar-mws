import time
import pytest

from django.test import TestCase

from oscar.test.factories import create_order

from oscar_mws import abstract_models as am
from oscar_mws.test import factories, mixins
from oscar_mws.feeds import gateway as feeds_gw
from oscar_mws.fulfillment.creator import FulfillmentOrderCreator


@pytest.mark.integration
class TestAFulfillmentOrder(mixins.IntegrationMixin, TestCase):

    def setUp(self):
        super(TestAFulfillmentOrder, self).setUp()
        self.basket = factories.BasketFactory()
        self.basket.add_product(self.product)
        shipping_address = factories.ShippingAddressFactory()
        self.order = create_order(shipping_address=shipping_address,
                                  basket=self.basket)

    def _wait_until_submission_processed(self, submission):
        while submission.processing_status not in [am.STATUS_DONE,
                                                   am.STATUS_CANCELLED]:
            time.sleep(20)  # wait before next polling to avoid throttling
            submission = feeds_gw.update_feed_submission(submission)

        if submission.processing_status != am.STATUS_DONE:
            raise Exception('Feed {} in unexpected state {}'.format(
                submission.submission_id, submission.processing_status))

        return submission

    def test_can_be_created(self):
        submissions = feeds_gw.submit_product_feed(
            products=[self.product], marketplaces=[self.marketplace])
        self._wait_until_submission_processed(submissions[0])

        submission = feeds_gw.switch_product_fulfillment(
            marketplace=self.marketplace, products=[self.product])
        self._wait_until_submission_processed(submission)

        creator = FulfillmentOrderCreator()
        orders = creator.create_fulfillment_order(self.order)
