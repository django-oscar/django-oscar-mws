from django.db.models import get_model
from django.core.urlresolvers import reverse

from oscar.test import factories
from oscar.test.testcases import WebTestCase

from oscar_mws.test.factories import AmazonMarketplaceFactory

AmazonProfile = get_model('oscar_mws', 'AmazonProfile')


class TestAmazonProfile(WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestAmazonProfile, self).setUp()
        self.product = factories.create_product()
        self.marketplace = AmazonMarketplaceFactory()

    def test_can_create_amazon_profile(self):
        create_page = self.get(
            reverse(
                'mws-dashboard:profile-create',
                kwargs={'pk': self.product.pk}
            )
        )

        profile_form = create_page.form
        profile_form['marketplaces'] = [self.marketplace.id]
        page = profile_form.submit()

        self.assertRedirects(page, reverse('mws-dashboard:profile-list'))

        profile = AmazonProfile.objects.get(product=self.product)
        self.assertEquals(profile.sku, self.product.stockrecord.partner_sku)
        self.assertSequenceEqual(
            profile.marketplaces.all(),
            [self.marketplace]
        )
