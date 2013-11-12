from django.test import TestCase
from django.db.models import get_model

from oscar_mws import receivers
from oscar_mws.test import factories

FulfillmentOrder = get_model('oscar_mws', 'FulfillmentOrder')


class TestSubmitOrderReceiver(TestCase):

    def setUp(self):
        super(TestSubmitOrderReceiver, self).setUp()
        self.user = factories.UserFactory()
        self.order = factories.OrderFactory(user=self.user)

    def test_skips_raw_import(self):
        receivers.submit_order_to_mws(self.order, self.user, raw=True)
        self.assertEquals(FulfillmentOrder.objects.count(), 0)
