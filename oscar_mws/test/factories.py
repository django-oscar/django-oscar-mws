import factory

from time import time
from decimal import Decimal as D

from django.utils.timezone import now
from django.db.models import get_model

from oscar.core.loading import get_class

from oscar_mws import MWS_MARKETPLACE_US

Selector = get_class('partner.strategy', 'Selector')


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('auth', 'User')

    first_name = 'Peter'
    last_name = 'Griffin'
    email = 'peter@petoria.pt'
    password = 'plaintext'


class CountryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('address', 'Country')

    iso_3166_1_a2 = factory.Iterator(['US', 'GB', 'DE'])
    iso_3166_1_a3 = factory.Iterator(['USA', 'GBR', 'DEU'])
    iso_3166_1_numeric = factory.Iterator(['840', '276', '826'])


class ProductClassFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'ProductClass')

    name = factory.Sequence(lambda n: 'Dummy product class {}'.format(n))


class BasketFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('basket', 'Basket')

    strategy = Selector().strategy()


class AmazonProfileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'AmazonProfile')
    FACTORY_DJANGO_GET_OR_CREATE = ('product',)

    sku = factory.Sequence(lambda n: "sku_{}".format(str(time())[:10]))
    release_date = now()
    product = factory.SubFactory(
        'oscar_mws.test.factories.ProductFactory', amazon_profile=None)


class ProductFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'Product')

    title = 'Dummy Product'
    product_class = factory.SubFactory(ProductClassFactory)
    amazon_profile = factory.RelatedFactory(AmazonProfileFactory, 'product')

    @factory.post_generation
    def stockrecord(self, created, extracted, **kwargs):
        if not created:
            return
        if not extracted:
            kwargs.setdefault('product', self)
            extracted = StockRecordFactory(**kwargs)
        self.stockrecords.add(extracted)


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
    marketplace_id = factory.Sequence(lambda n: 'MWS_MKT_{}'.format(n))
    merchant = factory.SubFactory(MerchantAccountFactory)


class FeedSubmissionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'FeedSubmission')
    FACTORY_DJANGO_GET_OR_CREATE = ('submission_id',)

    merchant = factory.SubFactory(MerchantAccountFactory)
    date_submitted = now()


class PartnerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('partner', 'Partner')

    name = factory.Sequence(lambda n: 'Dummy partner {}'.format(n))


class StockRecordFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('partner', 'StockRecord')

    price_excl_tax = D('12.99')
    partner = factory.SubFactory(PartnerFactory)
    product = factory.SubFactory(ProductFactory)


class ShippingAddressFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('order', 'ShippingAddress')

    first_name = 'Peter'
    last_name = 'Griffin'
    line1 = '31 Spooner Street'
    line4 = 'Quahog'
    state = 'RI'
    country = factory.SubFactory(CountryFactory)
    postcode = '12345'


class OrderLineFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('order', 'Line')

    product = factory.SubFactory(ProductFactory)
    line_price_excl_tax = D('12.99')
    line_price_incl_tax = D('12.99')
    line_price_before_discounts_incl_tax = D('12.99')
    line_price_before_discounts_excl_tax = D('12.99')


class OrderFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('order', 'Order')

    number = factory.Sequence(lambda n: "{}".format(10000 + n))
    site = factory.LazyAttribute(
        lambda a: get_model('sites', 'Site').objects.all()[0]
    )
    total_incl_tax = D('12.99')
    total_excl_tax = D('12.99')

    shipping_address = factory.SubFactory(ShippingAddressFactory)


class FulfillmentOrderFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'FulfillmentOrder')

    fulfillment_id = 'extern_id_1154539615776'
    merchant = factory.SubFactory(MerchantAccountFactory)
    date_updated = now()
    order = factory.SubFactory(OrderFactory)
    shipping_address = factory.SubFactory(ShippingAddressFactory)
