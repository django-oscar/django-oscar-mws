import logging
import oscar_mws

from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured

from . import api

logger = logging.getLogger('oscar_mws')


_mws_connections = {}


class Connection(object):
    API_CLASSES = {
        'feeds': api.Feeds,
        'outbound': api.OutboundShipments,
        'reports': api.Reports,
        'orders': api.Orders,
        'products': api.Products,
        'sellers': api.Sellers,
        'inbound': api.InboundShipments,
        'inventory': api.Inventory,
        'recommendations': api.Recommendations,
    }

    def __init__(self, merchant_id):
        MerchantAccount = get_model('oscar_mws', 'MerchantAccount')
        try:
            merchant = MerchantAccount.objects.get(seller_id=merchant_id)
        except MerchantAccount.DoesNotExist:
            raise ImproperlyConfigured(
                "Could not find merchant with ID {0}".format(merchant_id)
            )
        self.merchant_id = merchant_id
        self.access_key = merchant.aws_api_key
        self.secret_key = merchant.aws_api_secret
        self.region_endpoint = self.get_endpoint(merchant.region)

    def get_connection_kwargs(self):
        return {
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'account_id': self.merchant_id,
            'domain': "https://{0}".format(self.region_endpoint),
        }

    def get_endpoint(self, region):
        return oscar_mws.MWS_REGION_ENDPOINTS.get(region, None)

    def get_api_class(self, name):
        try:
            conn = self.API_CLASSES[name]
        except KeyError:
            raise ImproperlyConfigured(
                'API {0} is not a valid MWS API class'.format(name))
        return conn(**self.get_connection_kwargs())


def get_merchant_connection(merchant_id, api_name):
    global _mws_connections

    if merchant_id in _mws_connections:
        return _mws_connections[merchant_id].get_api_class(api_name)

    try:
        connection = Connection(merchant_id)
    except ImproperlyConfigured as exc:
        logger.error(exc.message)
        return None

    _mws_connections[merchant_id] = connection
    return _mws_connections[merchant_id].get_api_class(api_name)


def reset_connections():
    """
    Reset the connection cache to allow for changes in connection settings
    to take effect.
    """
    global _mws_connections
    _mws_connections = {}
