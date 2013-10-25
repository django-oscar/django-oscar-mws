import httpretty

from django.test import TestCase

from oscar_mws.seller import gateway
from oscar_mws.test import mixins, factories


class TestMarketplaces(mixins.DataLoaderMixin, TestCase):

    @httpretty.activate
    def test_can_be_updated_from_mws(self):
        xml = self.load_data('list_marketplace_participations_response.xml')
        httpretty.register_uri(
            httpretty.GET,
            'https://mws.amazonservices.com/Sellers/2011-07-01',
            body=xml,
        )

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
