import os
import time
import pytest

from django.test import TestCase

from oscar.test.factories import create_product

from oscar_mws.test import factories
from oscar_mws.models import AmazonProfile
from oscar_mws import abstract_models as am
from oscar_mws.feeds import gateway as feeds_gw


@pytest.mark.integration
class TestSubmittingAFeed(TestCase):

    def setUp(self):
        self.product = create_product(
            upc='9781741173420',
            title='Kayaking Around Australia',
        )
        self.merchant = factories.MerchantAccountFactory(
            name="Integration Test Account",
            seller_id=os.getenv('SELLER_ID'),
            aws_api_key=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_api_secret=os.getenv('AWS_SECRET_ACCESS_KEY'),
        )
        self.marketplace = factories.AmazonMarketplaceFactory(
            merchant=self.merchant,
            marketplace_id='ATVPDKIKX0DER',
        )

        amazon_profile = AmazonProfile.objects.create(product=self.product)
        amazon_profile.fulfillment_by = AmazonProfile.FULFILLMENT_BY_AMAZON
        amazon_profile.save()

        amazon_profile.marketplaces.add(self.marketplace)

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
            AmazonProfile.FULFILLMENT_BY_AMAZON
        )

        # Delete product
        submissions = feeds_gw.submit_product_feed(
            products=[self.product],
            marketplaces=[self.marketplace],
            operation_type=feeds_gw.OP_TYPE_DELETE,
        )
        submission = self._check_submission(submissions[0])
        self.assertEquals(submission.processing_status, am.STATUS_DONE)
