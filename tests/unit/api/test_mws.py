# -*- encoding: utf-8 -*-
from django.utils.unittest import TestCase

from oscar_mws import api


class TestApiRequest(TestCase):

    def setUp(self):
        self.mws = api.MWS('FAKE_KEY', 'FAKE_SECRET', 'FAKE_SELLER')

    def test_unicode_parameters_are_quoted_correctly(self):
        params = {'city': u'Düsseldorf', 'state': 'NRW'}
        self.assertEquals(
            self.mws._get_quote_params(params),
            'city=D%C3%BCsseldorf&state=NRW'
        )


class TestEnumerateParams(TestCase):

    def setUp(self):
        self.mws = api.MWS('FAKE_KEY', 'FAKE_SECRET', 'FAKE_SELLER')

    def test_returns_emtpy_dict_if_no_values_provided(self):
        self.assertEquals(self.mws.enumerate_param('Invalid.Id', None), {})

    def test_returns_enumerated_values_as_dict(self):
        self.assertItemsEqual(
            self.mws.enumerate_param('SomeValue.Id', ['12ABC', 'TEST']),
            {'SomeValue.Id.1': '12ABC', 'SomeValue.Id.2': 'TEST'}
        )


class TestDictParams(TestCase):

    def setUp(self):
        self.mws = api.MWS('FAKE_KEY', 'FAKE_SECRET', 'FAKE_SELLER')

    def test_returns_empty_dict_if_value_are_none(self):
        self.assertEquals(
            self.mws.dict_param('TestValue', {'Invalid': None}), {})

    def test_returns_dict_which_simple_key_value(self):
        self.assertEquals(
            self.mws.dict_param('TestValue', {'Id': 12}),
            {'TestValue.Id': 12}
        )

    def test_returns_dict_which_nested_key_values(self):
        dct = {'Item': {'Id': 12, 'Name': 'test name'}}
        self.assertEquals(
            self.mws.dict_param('TestValue', dct),
            {'TestValue.Item.Id': 12, 'TestValue.Item.Name': 'test name'}
        )


class TestRemoveEmptyhelper(TestCase):

    def test_returns_dict_without_empty_values(self):
        test_dct = {
            'key1': 'has a value',
            'key2': '',
            'key3': [],
            'key4': 23112,
            'key5': None,
        }
        self.assertItemsEqual(api.remove_empty(test_dct),
                              {'key1': 'has a value', 'key4': 23112})
