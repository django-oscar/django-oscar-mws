from django.contrib import admin

from django.db.models import get_model


admin.site.register(get_model("oscar_mws", "FeedSubmission"))
admin.site.register(get_model("oscar_mws", "FeedReport"))
admin.site.register(get_model("oscar_mws", "FeedResult"))
admin.site.register(get_model("oscar_mws", "AmazonProfile"))
admin.site.register(get_model("oscar_mws", "ShipmentPackage"))
admin.site.register(get_model("oscar_mws", "FulfillmentOrder"))
admin.site.register(get_model("oscar_mws", "FulfillmentOrderLine"))
admin.site.register(get_model("oscar_mws", "FulfillmentShipment"))
