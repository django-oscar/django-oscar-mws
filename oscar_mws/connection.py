import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from boto.mws.connection import MWSConnection


_mws_connection = None


def get_connection(aws_access_key_id=None, aws_secret_access_key=None,
                   **kwargs):
    global _mws_connection
    if not aws_access_key_id:
        aws_access_key_id = getattr(
            settings,
            'AWS_ACCESS_KEY_ID',
            os.environ.get('AWS_ACCESS_KEY_ID')
        )
    if not aws_secret_access_key:
        aws_secret_access_key = getattr(
            settings,
            'AWS_SECRET_ACCESS_KEY',
            os.environ.get('AWS_SECRET_ACCESS_KEY')
        )

    try:
        merchant_id = settings.MWS_SELLER_ID
    except AttributeError:
        raise ImproperlyConfigured(
            "a merchant/seller ID is required to use Amazon MWS. "
            "Please set 'MWS_SELLER_ID' in your settings."
        )

    if not _mws_connection:
        _mws_connection = MWSConnection(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            Merchant=merchant_id,
            **kwargs
        )
    return _mws_connection
