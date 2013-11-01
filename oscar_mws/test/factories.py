import factory

from time import time
from decimal import Decimal as D

from django.utils.timezone import now
from django.db.models import get_model

from oscar.core.loading import get_class

from oscar_mws import MWS_MARKETPLACE_US

Selector = get_class('partner.strategy', 'Selector')


class ProductClassFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'ProductClass')

    name = factory.Sequence(lambda n: 'Dummy product class {}'.format(n))


class ProductFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'Product')

    title = 'Dummy Product'
    product_class = factory.SubFactory(ProductClassFactory)

    @factory.post_generation
    def stockrecord(self, created, extracted, **kwargs):
        if not created:
            return
        if not extracted:
            kwargs.setdefault('product', self)
            extracted = StockRecordFactory(**kwargs)
        self.stockrecords.add(extracted)


class BasketFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('basket', 'Basket')

    strategy = Selector().strategy()


class AmazonProfileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'AmazonProfile')

    sku = factory.Sequence(lambda n: "sku_{}".format(str(time())[:10]))
    release_date = now()
    product = factory.SubFactory(ProductFactory)


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


class PartnerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('partner', 'Partner')

    name = factory.Sequence(lambda n:'Dummy partner {}'.format(n))


class StockRecordFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('partner', 'StockRecord')

    price_excl_tax = D('12.99')
    partner = factory.SubFactory(PartnerFactory)
