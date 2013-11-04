import time
import pytest

from django.test import TestCase

from oscar.test.factories import create_order

from oscar_mws import abstract_models as am
from oscar_mws.test import factories, mixins
from oscar_mws.feeds import gateway as feeds_gw
from oscar_mws.fulfillment.creator import FulfillmentOrderCreator


@pytest.mark.integration
class TestSubmittingAFeed(mixins.IntegrationMixin, TestCase):

    def _check_submission(self, submission):
        self.assertEquals(submission.processing_status, am.STATUS_SUBMITTED)

        while submission.processing_status not in [am.STATUS_DONE, am.STATUS_CANCELLED]:
            time.sleep(30)  # wait before next polling to avoid throttling
            submission = feeds_gw.update_feed_submission(submission)

        return submission

    def test_can_be_cancelled(self):
        submissions = feeds_gw.submit_product_feed(
            products=[self.product],
            marketplaces=[self.marketplace]
        )
        submission = submissions[0]
        self.assertEquals(submission.processing_status, am.STATUS_SUBMITTED)

        # we need to wait a bit before we can cancel the submission just to
        # make sure that it is available in the system
        time.sleep(2)
        submission = feeds_gw.cancel_submission(submission)

        # we need to wait again to make sure we get the proper result for the
        # feed submission ID
        time.sleep(5)
        submission = feeds_gw.update_feed_submission(submission)

        self.assertEquals(submission.processing_status, am.STATUS_CANCELLED)

    def test_is_processed(self):
        submissions = feeds_gw.submit_product_feed(
            products=[self.product],
            marketplaces=[self.marketplace]
        )
        submission = self._check_submission(submissions[0])
        self.assertEquals(submission.processing_status, am.STATUS_DONE)

        # Switch the product to FBA
        submission = feeds_gw.switch_product_fulfillment(
            marketplace=self.marketplace,
            products=[self.product],
        )
        submission = self._check_submission(submission)
        self.assertEquals(submission.processing_status, am.STATUS_DONE)

        feeds_gw.update_product_identifiers(
            submission.merchant,
            products=[self.product]
        )

        self.assertEquals(
            self.product.amazon_profile.fulfillment_by,
            self.product.amazon_profile.FULFILLMENT_BY_AMAZON
        )

        # Delete product
        submissions = feeds_gw.submit_product_feed(
            products=[self.product],
            marketplaces=[self.marketplace],
            operation_type=feeds_gw.OP_TYPE_DELETE,
        )
        submission = self._check_submission(submissions[0])
        self.assertEquals(submission.processing_status, am.STATUS_DONE)


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
