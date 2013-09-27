import factory

from django.utils.timezone import now
from django.db.models import get_model

from oscar_mws import MWS_MARKETPLACE_US


class MerchantAccountFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'MerchantAccount')

    name = "Dummy Merchant"
    seller_id = 'ASLLRIDHERE1J56'
    aws_api_key = 'FAKE_KEY'
    aws_api_secret = 'FAKE_SECRET'


class AmazonMarketplaceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'AmazonMarketplace')

    name = "Dummy Marketplace"
    region = MWS_MARKETPLACE_US
    marketplace_id = 'FAKEMARKETPLACEID'
    merchant = factory.SubFactory(MerchantAccountFactory)


class FulfillmentOrderFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'FulfillmentOrder')

    fulfillment_id = 'extern_id_1154539615776'
    merchant = factory.SubFactory(MerchantAccountFactory)
    date_updated = now()


class FeedSubmissionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'FeedSubmission')

    merchant = factory.SubFactory(MerchantAccountFactory)
    date_submitted = now()
