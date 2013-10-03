def default_merchant_finder(order, shipping_address, **kwargs):
    from django.db.models import get_model
    try:
        return get_model('oscar_mws', 'MerchantAccount').objects.all()[0]
    except IndexError:
        pass
    return None
