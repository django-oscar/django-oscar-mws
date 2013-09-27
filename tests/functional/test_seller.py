import mock

from django.test import TestCase

from oscar_mws.seller import gateway
from oscar_mws.test import mixins, factories


class TestMarketplaces(mixins.DataLoaderMixin, TestCase):

    def setUp(self):
        super(TestMarketplaces, self).setUp()

    def test_can_be_updated_from_mws(self):
        from boto.connection import AWSQueryConnection

        xml = self.load_data('list_marketplace_participations_response.xml')
        response = mock.Mock()
        response.read = mock.Mock(return_value=xml)
        response.status = 200

        AWSQueryConnection._mexe = mock.Mock(return_value=response)

        self.merchant = factories.MerchantAccountFactory(
            seller_id='ASLLRIDHERE1J56'
        )

        self.assertEquals(self.merchant.marketplaces.count(), 0)

        gateway.update_marketplaces(self.merchant)

        self.assertEquals(self.merchant.marketplaces.count(), 1)

        marketplace = self.merchant.marketplaces.all()[0]
        self.assertEquals(marketplace.marketplace_id, 'ATVPDKIKX0DER')
        self.assertEquals(marketplace.domain, 'www.amazon.com')
        self.assertEquals(marketplace.name, 'Amazon.com')
        self.assertEquals(marketplace.currency_code, 'USD')
        self.assertEquals(marketplace.region, 'US')
