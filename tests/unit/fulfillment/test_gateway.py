import mock

from django.test import TestCase

from oscar_mws.api import MWSError
from oscar_mws.test import factories
from oscar_mws.fulfillment import gateway


class TestSubmittingFulfillmentOrder(TestCase):

    def setUp(self):
        super(TestSubmittingFulfillmentOrder, self).setUp()
        self.fulfillment_order = factories.FulfillmentOrderFactory()

    def create_connection_mock(self, **kwargs):
        outbound = mock.Mock()
        outbound.create_fulfillment_order = mock.Mock(**kwargs)
        self.connection_mock = mock.Mock()
        self.connection_mock.outbound = outbound

    def test_sets_order_status_to_failed_with_error(self):
        self.create_connection_mock(side_effect=MWSError())

        with mock.patch('oscar_mws.fulfillment.gateway.get_merchant_connection') as gmc_mock:
            gmc_mock.return_value = self.connection_mock

            gateway.submit_fulfillment_orders([self.fulfillment_order])
            self.assertEquals(self.fulfillment_order.status,
                                self.fulfillment_order.SUBMISSION_FAILED)

    def test_sets_order_status_to_submitted_when_successful(self):
        self.create_connection_mock()

        with mock.patch('oscar_mws.fulfillment.gateway.get_merchant_connection') as gmc_mock:
            gmc_mock.return_value = self.connection_mock

            gateway.submit_fulfillment_orders([self.fulfillment_order])
            self.assertEquals(self.fulfillment_order.status,
                                self.fulfillment_order.SUBMITTED)
