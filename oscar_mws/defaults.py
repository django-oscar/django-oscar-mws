import os

MWS_SELLER_ID = os.environ.get("MWS_SELLER_ID")
MWS_MARKETPLACE_ID = os.environ.get("MWS_MARKETPLACE_ID")
# Django ORM field description for seller SKU relative to Product model
MWS_SELLER_SKU_FIELD = 'stockrecord__partner_sku'

OSCAR_MWS_SETTINGS = dict(
    [(k, v) for k, v in locals().items() if k.startswith('MWS')]
)
