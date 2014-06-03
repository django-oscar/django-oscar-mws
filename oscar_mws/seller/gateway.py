import logging

from django.db.models import get_model

from ..api import MWSError
from ..connection import get_merchant_connection

logger = logging.getLogger('oscar_mws')

AmazonMarketplace = get_model('oscar_mws', 'AmazonMarketplace')


def update_marketplaces(merchant):
    sellers_api = get_merchant_connection(merchant.seller_id, 'sellers')

    try:
        response = sellers_api.list_marketplace_participations().parsed
    except MWSError:
        logger.error(
            "could not retrieve marketplaces for merchant {}".format(
                merchant.seller_id),
            exc_info=1, extra={'seller_id': merchant.seller_id})
        return []

    marketplaces = []
    for rsp_marketplace in response.ListMarketplaces.get_list('Marketplace'):
        try:
            marketplace = AmazonMarketplace.objects.get(
                marketplace_id=rsp_marketplace.MarketplaceId,
                merchant=merchant)
        except AmazonMarketplace.DoesNotExist:
            marketplace = AmazonMarketplace(
                marketplace_id=rsp_marketplace.MarketplaceId,
                merchant=merchant)
        marketplace.name = rsp_marketplace.Name
        marketplace.domain = rsp_marketplace.DomainName
        marketplace.region = rsp_marketplace.DefaultCountryCode
        marketplace.currency_code = rsp_marketplace.DefaultCurrencyCode
        marketplace.save()

        marketplaces.append(marketplace)
    return marketplaces
