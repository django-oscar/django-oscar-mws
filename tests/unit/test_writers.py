import mock

from lxml import etree

from django.test import TestCase
from django.db.models import get_model
from django.utils.timezone import now

from oscar_testsupport.factories import create_product

from oscar_mws.writers import ProductFeedWriter, BaseProductMapper

UTC_NOW = now()

AmazonProfile = get_model('oscar_mws', 'AmazonProfile')


class TestProductFeedWriter(TestCase):

    def test_generate_valid_xml(self):
        writer = ProductFeedWriter(merchant_id='MERCH_X_123')

        product = create_product()
        product.description = """Lyric sheeting by Peacock Alley is the epitome of simple and classic elegance. The flat sheets
and pillowcases feature a double row of hemstitching. The fitted sheets fit mattresses up to 21 inches deep.
The sheets are shown at left with tone on tone monogramming, please call for monogramming details and prices.
Please note, gift wrapping and overnight shipping are not available for this style."""
        AmazonProfile.objects.create(
            product=product,
            release_date=UTC_NOW.replace(year=UTC_NOW.year+4)
        )
        writer.add_product(product)

        feed = writer.as_string()
        self.assertIn(
            "<MerchantIdentifier>MERCH_X_123</MerchantIdentifier>",
            feed
        )
        self.assertIn(
            "<Description>{0}</Description>".format(product.description),
            feed
        )


class TestBaseProductMapper(TestCase):

    def test_gets_value_from_object_attribute(self):
        class Mock(object):
            pass

        obj = Mock()
        obj.test_attribute = 'amazing value'

        mapper = BaseProductMapper()
        self.assertEquals(
            mapper._get_value_from(obj, 'test_attribute'),
            obj.test_attribute
        )

    def test_gets_value_from_object_getter(self):
        obj = mock.Mock()
        obj.get_test_attribute = mock.Mock(return_value='amazing value')

        mapper = BaseProductMapper()
        self.assertEquals(
            mapper._get_value_from(obj, 'test_attribute'),
            obj.get_test_attribute()
        )

    def test_can_create_feed_for_base_attributes(self):
        product = create_product()

        AmazonProfile.objects.create(
            product=product,
            release_date=UTC_NOW
        )

        mapper = BaseProductMapper()
        xml = etree.tostring(mapper.get_product_xml(product))
        self.assertIn(
            '<SKU>{0}</SKU>'.format(product.stockrecord.partner_sku),
            xml
        )
        self.assertIn(
            '<ReleaseDate>{0}</ReleaseDate>'.format(UTC_NOW.isoformat()),
            xml
        )
        self.assertIn('<Title>{0}</Title>'.format(product.title), xml)
