import mock

from django.test import TestCase

from oscar_testsupport.factories import create_product

from oscar_mws.writers import ProductFeedWriter, BaseProductMapper


class TestProductFeedWriter(TestCase):

    def test_generate_valid_xml(self):
        writer = ProductFeedWriter('121231')
        print writer.as_string()


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

    def test_raises_attribute_error_if_not_available(self):
        class Mock(object):
            pass
        obj = Mock()
        mapper = BaseProductMapper()
        self.assertRaises(
            AttributeError,
            mapper._get_value_from,
            obj, 'test_attribute'
        )
