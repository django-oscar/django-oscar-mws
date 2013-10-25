import os

from django.test import TestCase

from oscar.test.factories import create_product

from oscar_mws.test import factories
#from oscar_mws.models import MerchantAccount
#from oscar_mws.connection import get_merchant_connection
from oscar_mws.feeds import gateway as feeds_gw


class TestSubmittingFeed(TestCase):

    def setUp(self):
        self.product = create_product()
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

    def test_for_a_single_product(self):
        #sellers_api = get_merchant_connection(self.merchant.seller_id).sellers
        #print sellers_api.list_marketplace_participations().parsed
        feeds_gw.submit_product_feed(
            products=[self.product],
            marketplaces=[self.marketplace]
        )


        #feeds_api.submit_product_feed(products=[self.product])
