import logging

from django.db.models import get_model

from boto.mws.connection import MWSConnection

logger = logging.getLogger('oscar_mws')

MerchantAccount = get_model('oscar_mws', 'MerchantAccount')


_mws_connections = {}


def get_connection(merchant_id, aws_access_key_id, aws_secret_access_key,
                   **kwargs):
    global _mws_connections

    _mws_connections[merchant_id] = MWSConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        SellerId=merchant_id,
        **kwargs
    )
    return _mws_connections[merchant_id]


def get_merchant_connection(merchant_id):
    global _mws_connections

    print merchant_id, _mws_connections

    if merchant_id in _mws_connections:
        return _mws_connections[merchant_id]

    try:
        merchant = MerchantAccount.objects.get(seller_id=merchant_id)
    except MerchantAccount.DoesNotExist:
        logger.error(
            "Could not find merchant with ID {0}".format(merchant_id)
        )
        return

    return get_connection(
        merchant_id,
        aws_access_key_id=merchant.aws_api_key,
        aws_secret_access_key=merchant.aws_api_secret,
    )
