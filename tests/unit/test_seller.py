import mock
import httpretty

from django.test import TestCase
from django.db.models import get_model

from oscar_mws.test import mixins



class TestMarketplaces(mixins.DataLoaderMixin, TestCase):

    def test_can_be_updated_from_mws(self):
        pass
