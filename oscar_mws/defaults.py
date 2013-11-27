from django.utils.translation import ugettext_lazy as _

# Callable that returns an appropriate region for a given order and address
MWS_FULFILLMENT_MERCHANT_FINDER = \
    'oscar_mws.fulfillment.finders.default_merchant_finder'

MWS_DEFAULT_SHIPPING_SPEED = 'Standard'

MWS_DASHBOARD_NAVIGATION = [
    {
        'label': _('Amazon MWS'),
        'icon': 'icon-truck',
        'children': [
            {
                'label': _('Profiles'),
                'url_name': 'mws-dashboard:profile-list',
            },
            {
                'label': _('Merchants & Marketplaces'),
                'url_name': 'mws-dashboard:merchant-list',
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
