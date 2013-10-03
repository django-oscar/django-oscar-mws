from django.utils.translation import ugettext_lazy as _


SHIPPING_STANDARD = 'Standard'
SHIPPING_EXPEDITED = 'Expedited'
SHIPPING_PRIORITY = 'Priority'

SHIPPING_SPEED_CATEGORIES = (
    (SHIPPING_STANDARD, _("Standard")),
    (SHIPPING_EXPEDITED, _("Expedited")),
    (SHIPPING_PRIORITY, _("Priority")),
)

METHOD_CONSUMER = 'Consumer'
METHOD_REMOVAL = 'Removal'

FULFILLMENT_METHODS = (
    (METHOD_CONSUMER, _("Consumer")),
    (METHOD_REMOVAL, _("Removal")),
)

FILL_OR_KILL = 'FillOrKill'
FILL_ALL = 'FillAll'
FILL_ALL_AVAILABLE = 'FillAllAvailable'


class MwsFulfillmentError(BaseException):
    pass
