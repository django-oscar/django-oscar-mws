import django.dispatch

mws_fulfillment_created = django.dispatch.Signal(
    providing_args=["fulfillment_order", "user"])
