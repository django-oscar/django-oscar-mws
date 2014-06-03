import mock

from django.test import TestCase

from oscar_mws.api import MWSError
from oscar_mws.test import factories
from oscar_mws.fulfillment import gateway


class TestSubmittingFulfillmentOrder(TestCase):

    def setUp(self):
        super(TestSubmittingFulfillmentOrder, self).setUp()
        self.fulfillment_order = factories.FulfillmentOrderFactory()

    def test_sets_order_status_to_failed_with_error(self):
        with mock.patch('oscar_mws.fulfillment.gateway.get_merchant_connection') as gmc_mock:
            gmc_mock.return_value = mock.Mock(
                create_fulfillment_order=mock.Mock(side_effect=MWSError()))

            gateway.submit_fulfillment_orders([self.fulfillment_order])
            self.assertEquals(self.fulfillment_order.status,
                                self.fulfillment_order.SUBMISSION_FAILED)

    def test_sets_order_status_to_submitted_when_successful(self):
        with mock.patch('oscar_mws.fulfillment.gateway.get_merchant_connection') as gmc_mock:
            gmc_mock.return_value = mock.Mock(
                create_fulfillment_order=mock.Mock())

            gateway.submit_fulfillment_orders([self.fulfillment_order])
            self.assertEquals(self.fulfillment_order.status,
                                self.fulfillment_order.SUBMITTED)
