# -*- encoding: utf-8 -*-
from mock import Mock

from django.utils.unittest import TestCase

from oscar_mws import api


class TestOutboundShipments(TestCase):

    def setUp(self):
        super(TestOutboundShipments, self).setUp()
        self.outbound = api.OutboundShipments('FK', 'FK', 'A2NKEXAMPLEF53')
        self.outbound.make_request = Mock()
        self.address = {
            'Name': 'James Smith',
            'Line1': '456 Cedar St',
            'City': 'Seattle',
            'StateOrProvinceCode': 'WA',
            'PostalCode': '98104',
            'CountryCode': 'US',
        }
        self.items = [
            {'SellerSKU': 'SampleSKU1', 'Quantity': 1,
             'SellerFulfillmentOrderItemId': 'TestId1'},
            {'SellerSKU': 'SampleSKU2', 'Quantity': 2,
             'SellerFulfillmentOrderItemId': 'TestId2'},
        ]

    def test_create_fulfillment_preview(self):
        shipping_speeds = ['Expedited', 'Standard']
        self.outbound.get_fulfillment_preview(
            address=self.address, items=self.items,
            shipping_speed_categories=shipping_speeds)
        expected_params = {
            'Action': 'GetFulfillmentPreview',
            'ShippingSpeedCategories.1': 'Expedited',
            'ShippingSpeedCategories.2': 'Standard',
            'Address.Name': 'James Smith',
            'Address.Line1': '456 Cedar St',
            'Address.City': 'Seattle',
            'Address.StateOrProvinceCode': 'WA',
            'Address.PostalCode': '98104',
            'Address.CountryCode': 'US',
            'Items.member.1.Quantity': 1,
            'Items.member.1.SellerFulfillmentOrderItemId': 'TestId1',
            'Items.member.1.SellerSKU': 'SampleSKU1',
            'Items.member.2.Quantity': 2,
            'Items.member.2.SellerFulfillmentOrderItemId': 'TestId2',
            'Items.member.2.SellerSKU': 'SampleSKU2',
        }
        self.assertItemsEqual(
            self.outbound.make_request.call_args[0][0], expected_params)
        self.assertItemsEqual(
            self.outbound.make_request.call_args[0][1], 'GET')

    def test_create_fulfillment_order_with_only_required_params(self):
        self.outbound.create_fulfillment_order(
            order_id='100001', items=self.items, comments="Thanks!",
            destination_address=self.address, order_date='2010-12-31T17:17:42',
            shipping_speed='Standard')

        expected_params = {
            'Action': 'CreateFulfillmentOrder',
            'SellerFulfillmentOrderId': '100001',
            'DestinationAddress.Name': 'James Smith',
            'DestinationAddress.Line1': '456 Cedar St',
            'DestinationAddress.City': 'Seattle',
            'DestinationAddress.StateOrProvinceCode': 'WA',
            'DestinationAddress.PostalCode': '98104',
            'DestinationAddress.CountryCode': 'US',
            'Items.member.1.Quantity': 1,
            'Items.member.1.SellerFulfillmentOrderItemId': 'TestId1',
            'Items.member.1.SellerSKU': 'SampleSKU1',
            'Items.member.2.Quantity': 2,
            'Items.member.2.SellerFulfillmentOrderItemId': 'TestId2',
            'Items.member.2.SellerSKU': 'SampleSKU2',
            'DisplayableOrderDateTime': '2010-12-31T17:17:42',
            'DisplayableOrderId': '100001',
            'DisplayableOrderComment': 'Thanks!',
            'DisplayableOrderDateTime': '2010-12-31T17:17:42',
            'ShippingSpeedCategory': 'Standard',
        }
        self.assertItemsEqual(
            self.outbound.make_request.call_args[0][0], expected_params)
        self.assertItemsEqual(
            self.outbound.make_request.call_args[0][1], 'POST')

    def test_create_fulfillment_order_with_optional_params(self):
        self.outbound.create_fulfillment_order(
            order_id='100001', items=self.items, comments="Thanks!",
            destination_address=self.address, order_date='2010-12-31T17:17:42',
            shipping_speed='Standard', fulfillment_method='Consumer',
            fulfillment_policy='FillOrKill')

        expected_params = {
            'Action': 'CreateFulfillmentOrder',
            'SellerFulfillmentOrderId': '100001',
            'DestinationAddress.Name': 'James Smith',
            'DestinationAddress.Line1': '456 Cedar St',
            'DestinationAddress.City': 'Seattle',
            'DestinationAddress.StateOrProvinceCode': 'WA',
            'DestinationAddress.PostalCode': '98104',
            'DestinationAddress.CountryCode': 'US',
            'Items.member.1.Quantity': 1,
            'Items.member.1.SellerFulfillmentOrderItemId': 'TestId1',
            'Items.member.1.SellerSKU': 'SampleSKU1',
            'Items.member.2.Quantity': 2,
            'Items.member.2.SellerFulfillmentOrderItemId': 'TestId2',
            'Items.member.2.SellerSKU': 'SampleSKU2',
            'DisplayableOrderDateTime': '2010-12-31T17:17:42',
            'DisplayableOrderId': '100001',
            'DisplayableOrderComment': 'Thanks!',
            'DisplayableOrderDateTime': '2010-12-31T17:17:42',
            'ShippingSpeedCategory': 'Standard',
            'FulfillmentMethod': 'Consumer',
            'FulfillmentPolicy': 'FillOrKill',
        }
        self.assertItemsEqual(
            self.outbound.make_request.call_args[0][0], expected_params)
        self.assertItemsEqual(
            self.outbound.make_request.call_args[0][1], 'POST')
