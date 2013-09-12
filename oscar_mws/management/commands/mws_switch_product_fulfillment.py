from optparse import make_option

from django.conf import settings
from django.db.models import get_model
from django.core.management.base import NoArgsCommand, CommandError

from oscar_mws.feeds.gateway import switch_product_fulfillment

Product = get_model('catalogue', 'Product')
AmazonProfile = get_model('oscar_mws', 'AmazonProfile')


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help=('Do not submit the inventory feed put print the generated '
                  'XML to stdout.')
        ),
        make_option(
            '--fulfilled-by',
            dest='fulfilled_by',
            help=('Switch fulfillment for all products to FULFILLED_BY')
        ),
    )

    def handle_noargs(self, **options):
        fulfilled_by = options.get('fulfilled_by')
        if not fulfilled_by:
            raise CommandError(
                "Fulfillment type is required but was not specified, please "
                "specify a fulfillment type (MFN or AFN)"
            )

        if fulfilled_by != AmazonProfile.FULFILLMENT_BY_AMAZON \
           and fulfilled_by != AmazonProfile.FULFILLMENT_BY_MERCHANT:
            raise CommandError(
                ("Invalid fulfillment type specified. Valid values are {0} "
                 " and {1}").format(
                    AmazonProfile.FULFILLMENT_BY_AMAZON,
                    AmazonProfile.FULFILLMENT_BY_MERCHANT,
                )
            )

        merchant_id = getattr(settings, 'MWS_SELLER_ID')

        submission = switch_product_fulfillment(
            products=Product.objects.all(),
            merchant_id=merchant_id,
            fulfillment_by=fulfilled_by,
            fulfillment_center_id="AMAZON_NA",
            dry_run=options.get('dry_run')
        )

        if not options.get('dry_run'):
            print "Feed submitted as ID #{0}".format(submission.submission_id)
