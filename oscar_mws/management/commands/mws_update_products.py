from optparse import make_option

from django.conf import settings
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.core.management.base import NoArgsCommand

from oscar_mws.feeds import gateway

Product = get_model('catalogue', 'Product')


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--lookup-asins',
            action='store_true',
            dest='lookup_asins',
            default=False,
            help=_('Updates the ASINs for all products without one.')
        ),
    )

    def handle_noargs(self, **options):
        if options.get('lookup_asins'):
            products = Product.objects.filter(
                amazon_profile__asin=''
            )
            gateway.update_product_identifiers(
                products,
                marketplace_id=settings.MWS_MARKETPLACE_ID
            )
