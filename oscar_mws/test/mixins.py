# -*- coding: utf-8 -*-
import os
import base64
import hashlib

from . import factories


class DataLoaderMixin(object):
    data_directory = 'tests/data'

    def get_md5(self, content):
        return base64.encodestring(hashlib.md5(content).digest()).strip()

    def get_data_directory(self):
        return os.path.join(os.getcwd(), self.data_directory)

    def load_data(self, filename):
        path = os.path.join(self.get_data_directory(), filename)
        data = None
        with open(path) as fh:
            data = fh.read()
        return data


class IntegrationMixin(object):

    def setUp(self):
        super(IntegrationMixin, self).setUp()

        self.product = factories.ProductFactory(
            upc='9781741173420', title='Kayaking Around Australia')

        self.merchant = factories.MerchantAccountFactory(
            name="Integration Test Account", seller_id=os.getenv('SELLER_ID'),
            aws_api_key=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_api_secret=os.getenv('AWS_SECRET_ACCESS_KEY'))

        amazon_profile = factories.AmazonProfileFactory(product=self.product)
        amazon_profile.fulfillment_by = amazon_profile.FULFILLMENT_BY_AMAZON
        amazon_profile.save()

        self.marketplace = factories.AmazonMarketplaceFactory(
            merchant=self.merchant, marketplace_id='ATVPDKIKX0DER')
        amazon_profile.marketplaces.add(self.marketplace)
