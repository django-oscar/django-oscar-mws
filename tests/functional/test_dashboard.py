from django.db.models import get_model
from django.core.urlresolvers import reverse

from oscar.test.testcases import WebTestCase

from oscar_mws.test import factories

AmazonProfile = get_model('oscar_mws', 'AmazonProfile')


class TestAmazonProfileDashboard(WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestAmazonProfileDashboard, self).setUp()
        self.product = factories.ProductFactory(amazon_profile=None)
        self.marketplace = factories.AmazonMarketplaceFactory()

        try:
            self.product.amazon_profile
        except AmazonProfile.DoesNotExist:
            pass
        else:
            self.fail("product has Amazon profile but shouldn't")

    def test_allows_to_create_profile_for_product(self):
        form = self.get(reverse('mws-dashboard:profile-create',
                        args=(self.product.pk,))).form
        form['sku'] = 'SAMPLE_SKU'
        form['marketplaces'] = (self.marketplace.id,)
        page = form.submit()
        self.assertRedirects(page, reverse('mws-dashboard:profile-list'))

        try:
            AmazonProfile.objects.get(product=self.product)
        except AmazonProfile.DoesNotExist:
            self.fail("Amazon profile not created")

    def test_displays_message_for_unkown_product(self):
        page = self.get(reverse('mws-dashboard:profile-create', args=(22222,)))
        self.assertRedirects(page, reverse('mws-dashboard:profile-list'))
