# -*- coding: utf-8 -*-
import os
import pytest

from oscar_mws.test import factories
from oscar_mws.seller.gateway import update_marketplaces


@pytest.fixture
def merchant(transactional_db):
    # make sure that the connection cache is cleared
    from oscar_mws import connection
    connection._mws_connections = {}

    merchant = factories.MerchantAccountFactory(
        name="Integration Test Account",
        seller_id=os.getenv('SELLER_ID'),
        aws_api_key=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_api_secret=os.getenv('AWS_SECRET_ACCESS_KEY'))
    return merchant


@pytest.mark.integration
def test_marketplaces_can_be_retrieved_for_merchant_account(merchant):
    assert merchant.marketplaces.count() == 0
    update_marketplaces(merchant)

    market_ids = [m.marketplace_id for m in merchant.marketplaces.all()]
    assert sorted(market_ids) == sorted([u'ATVPDKIKX0DER', u'A2ZV50J4W1RKNI'])


@pytest.mark.integration
def test_fails_gracefully_if_no_marketplace_found(merchant):
    assert merchant.marketplaces.count() == 0

    merchant.aws_api_key = 'invalidkey'
    merchant.aws_api_secret = 'invalidsecret'
    merchant.save()

    update_marketplaces(merchant)

    assert merchant.marketplaces.count() == 0
