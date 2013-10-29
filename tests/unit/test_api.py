# -*- encoding: utf-8 -*-
from django.utils.unittest import TestCase

from oscar_mws.api import MWS


class TestApiRequest(TestCase):

    def setUp(self):
        self.mws = MWS('FAKE_KEY', 'FAKE_SECRET', 'FAKE_SELLER')

    def test_unicode_parameters_are_quoted_correctly(self):
        params = {'city': u'Düsseldorf', 'state': 'NRW'}
        self.assertEquals(
            self.mws._get_quote_params(params),
            'city=D%C3%BCsseldorf&state=NRW'
        )
