import mock

from django.test import TestCase

from oscar_mws.api import MWSError
from oscar_mws.signals import mws_fulfillment_created
from oscar_mws.fulfillment.gateway import submit_fulfillment_order


class TestMwsFulfillmentCreatedSignal(TestCase):

    def test_is_emitted_when_successfully_submitted_to_mws(self):
        self.signal_sent = False
        fulfillment_order_mock = mock.Mock()
        fulfillment_order_mock.get_order_kwargs = mock.Mock(return_value={})

        def fake_receiver(fulfillment_order, **kwargs):
            self.signal_sent = True
            self.assertEquals(fulfillment_order, fulfillment_order_mock)

        mws_fulfillment_created.connect(fake_receiver)

        with mock.patch('oscar_mws.fulfillment.gateway.get_merchant_connection') as gmc_mock:
            connection_mock = mock.Mock()
            gmc_mock.return_value = connection_mock
            outbound_mock = mock.Mock()
            connection_mock.outbound = outbound_mock
            connection_mock.create_fulfillment_order = mock.Mock(
                return_value=None)

            submit_fulfillment_order(fulfillment_order_mock)

        if not self.signal_sent:
            self.fail("MWS order signal not sent")

    def test_is_not_emitted_when_sumitting_to_mws_fails(self):
        self.signal_sent = False
        fulfillment_order_mock = mock.Mock()
        fulfillment_order_mock.get_order_kwargs = mock.Mock(return_value={})

        def fake_receiver(fulfillment_order, **kwargs):
            self.signal_sent = True
            self.assertEquals(fulfillment_order, fulfillment_order_mock)

        mws_fulfillment_created.connect(fake_receiver)

        with mock.patch('oscar_mws.fulfillment.gateway.get_merchant_connection') as gmc_mock:
            connection_mock = mock.Mock()
            gmc_mock.return_value = connection_mock
            outbound_mock = mock.Mock()
            connection_mock.outbound = outbound_mock
            outbound_mock.create_fulfillment_order = mock.MagicMock(
                side_effect=MWSError())

            submit_fulfillment_order(fulfillment_order_mock)

        if self.signal_sent:
            self.fail("no signal should have been sent but was.")
