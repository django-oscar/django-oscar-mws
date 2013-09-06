from django import forms
from django.utils.translation import ugettext_lazy as _


class MwsProductFeedForm(forms.Form):
    FEED_CREATE_PRODUCTS = 'submit_product_feed'
    FEED_SWITCH_TO_AFN = 'switch_to_afn'
    UPDATE_PRODUCT_IDENTIFIERS = 'update_product_identifiers'
    FEED_CHOICES = (
        (FEED_CREATE_PRODUCTS, _("Create new products")),
        (FEED_SWITCH_TO_AFN, _("Switch to 'Fulfillment by Amazon'")),
        (UPDATE_PRODUCT_IDENTIFIERS, _("Update product ASINs")),
    )
    submission_selection = forms.ChoiceField(choices=FEED_CHOICES)
