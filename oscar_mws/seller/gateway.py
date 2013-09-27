from django.db.models import get_model

from ..connection import get_merchant_connection

AmazonMarketplace = get_model('oscar_mws', 'AmazonMarketplace')


def update_marketplaces(merchant):
    mws_conn = get_merchant_connection(merchant.seller_id)
    response = mws_conn.list_marketplace_participations()

    mp_list = response.ListMarketplaceParticipationsResult.ListMarketplaces
    marketplaces = []
    for rsp_marketplace in mp_list.Marketplace:
        try:
            marketplace = AmazonMarketplace.objects.get(
                marketplace_id=rsp_marketplace.MarketplaceId,
                merchant=merchant,
            )
        except AmazonMarketplace.DoesNotExist:
            marketplace = AmazonMarketplace(
                marketplace_id=rsp_marketplace.MarketplaceId,
                merchant=merchant,
            )
        marketplace.name = rsp_marketplace.Name
        marketplace.domain = rsp_marketplace.DomainName
        marketplace.region = rsp_marketplace.DefaultCountryCode
        marketplace.currency_code = rsp_marketplace.DefaultCurrencyCode
        marketplace.save()

        marketplaces.append(marketplace)
    return marketplaces
