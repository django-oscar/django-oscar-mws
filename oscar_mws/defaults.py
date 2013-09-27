import os

from django.utils.translation import ugettext_lazy as _


MWS_SELLER_ID = os.environ.get("MWS_SELLER_ID")
MWS_MARKETPLACE_ID = os.environ.get("MWS_MARKETPLACE_ID")
# Django ORM field description for seller SKU relative to Product model
MWS_SELLER_SKU_FIELD = 'stockrecord__partner_sku'

MWS_DEFAULT_SHIPPING_SPEED = 'Standard'

MWS_DASHBOARD_NAVIGATION = [
    {
        'label': _('Amazon MWS'),
        'icon': 'icon-truck',
        'children': [
            {
                'label': _('Products'),
                'url_name': 'mws-dashboard:product-list',
            },
            {
                'label': _('Merchants & Marketplaces'),
                'url_name': 'mws-dashboard:marketplace-list',
            },
            {
                'label': _('Feed submissions'),
                'url_name': 'mws-dashboard:submission-list',
            },
        ]
    }
]

OSCAR_MWS_SETTINGS = dict(
    [(k, v) for k, v in locals().items() if k.startswith('MWS')]
)
