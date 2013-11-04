from django import forms
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

AmazonMarketplace = get_model('oscar_mws', 'AmazonMarketplace')


class MwsProductFeedForm(forms.Form):
    FEED_CREATE_PRODUCTS = 'submit_product_feed'
    FEED_SWITCH_TO_AFN = 'switch_to_afn'
    UPDATE_PRODUCT_IDENTIFIERS = 'update_product_identifiers'
    UPDATE_STOCK = 'update_stock'
    FEED_CHOICES = (
        (FEED_CREATE_PRODUCTS, _("Create new products")),
        (FEED_SWITCH_TO_AFN, _("Switch to 'Fulfillment by Amazon'")),
        (UPDATE_PRODUCT_IDENTIFIERS, _("Update product ASINs")),
        (UPDATE_STOCK, _("Update product stock")),
    )
    submission_selection = forms.ChoiceField(choices=FEED_CHOICES)
    marketplace = forms.ModelChoiceField(
        queryset=AmazonMarketplace.objects.none(),
        required=True,
        empty_label=None,
        label=_("Marketplace"),
    )

    def __init__(self, *args, **kwargs):
        super(MwsProductFeedForm, self).__init__(*args, **kwargs)
        self.fields['marketplace'].queryset = AmazonMarketplace.objects.all()


class AmazonProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = get_model('oscar_mws', 'AmazonProfile')
        exclude = ('product', 'asin')


class AmazonProfileCreateForm(forms.ModelForm):
    class Meta:
        model = get_model('oscar_mws', 'AmazonProfile')
        exclude = ('asin',)

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product')
        super(AmazonProfileCreateForm, self).__init__(*args, **kwargs)
        self.fields['product'].initial = product
        self.fields['product'].widget = forms.HiddenInput()
