# -*- coding: utf-8 -*-
import os
import time
import pytest

from django.conf import settings
from django.test import TestCase

from oscar_mws.test import factories
from oscar_mws.models import AmazonProfile
from oscar_mws import abstract_models as am
from oscar_mws.feeds import gateway as feeds_gw

INTEGRATION_WAIT_TIME = settings.INTEGRATION_WAIT_TIME


@pytest.mark.integration
class TestSubmittingAFeed(TestCase):

    def setUp(self):
        self.product = factories.ProductFactory(
            upc='9781741173420', title='Kayaking Around Australia',
            amazon_profile=None)

        self.merchant = factories.MerchantAccountFactory(
            name="Integration Test Account",
            seller_id=os.getenv('SELLER_ID'),
            aws_api_key=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_api_secret=os.getenv('AWS_SECRET_ACCESS_KEY'))

        self.marketplace = factories.AmazonMarketplaceFactory(
            merchant=self.merchant, marketplace_id='ATVPDKIKX0DER')

        amazon_profile = factories.AmazonProfileFactory(
            product=self.product,
            fulfillment_by=AmazonProfile.FULFILLMENT_BY_AMAZON)

        amazon_profile.marketplaces.add(self.marketplace)

    def _check_submission(self, submission):
        self.assertEquals(submission.processing_status, am.STATUS_SUBMITTED)

        statuses = [am.STATUS_DONE, am.STATUS_CANCELLED]
        while submission.processing_status not in statuses:
            time.sleep(INTEGRATION_WAIT_TIME)
            submission = feeds_gw.update_feed_submission(submission)

        time.sleep(1)
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
        time.sleep(INTEGRATION_WAIT_TIME)
        submission = feeds_gw.update_feed_submission(submission)

        if submission.processing_status == am.STATUS_IN_PROGRESS:
            self.fail("submission was cancelled too late, processing was "
                      "already in progress")

        self.assertEquals(submission.processing_status, am.STATUS_CANCELLED)

    def test_is_processed(self):
        submissions = feeds_gw.submit_product_feed(
            products=[self.product], marketplaces=[self.marketplace])

        submission = self._check_submission(submissions[0])
        self.assertEquals(submission.processing_status, am.STATUS_DONE)

        # Switch the product to FBA
        submission = feeds_gw.switch_product_fulfillment(
            marketplace=self.marketplace, products=[self.product])

        submission = self._check_submission(submission)
        self.assertEquals(submission.processing_status, am.STATUS_DONE)

        feeds_gw.update_product_identifiers(
            submission.merchant, products=[self.product])

        self.assertEquals(
            self.product.amazon_profile.fulfillment_by,
            AmazonProfile.FULFILLMENT_BY_AMAZON)

        # Delete product
        submissions = feeds_gw.submit_product_feed(
            products=[self.product],
            marketplaces=[self.marketplace],
            operation_type=feeds_gw.OP_TYPE_DELETE)

        submission = self._check_submission(submissions[0])
        self.assertEquals(submission.processing_status, am.STATUS_DONE)
