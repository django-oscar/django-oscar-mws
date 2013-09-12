from optparse import make_option

from django.db.models import get_model
from django.core.management.base import NoArgsCommand, CommandError

from oscar_mws.feeds import gateway

Product = get_model('catalogue', 'Product')
FeedSubmission = get_model('oscar_mws', 'FeedSubmission')


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--list',
            action='store_true',
            dest='list_feeds',
            default=False,
            help=('List all feed from Amazon including type and status.')
        ),
        make_option(
            '--submission',
            dest='submission_id',
            help=('Submission ID to retrieve details results for.')
        ),
    )

    def handle_noargs(self, **options):
        if options.get('list_feeds'):
            for feed in gateway.list_submitted_feeds():
                print "{0}\t\t{1}\t\t{2}".format(
                    feed['submission_id'],
                    feed['feed_type'],
                    feed['status'],
                )
            return

        submission_id = options.get('submission_id')
        if submission_id:
            submission = gateway.update_feed_submission(submission_id)

            try:
                submission = FeedSubmission.objects.get(
                    submission_id=submission_id
                )
            except FeedSubmission.DoesNotExist:
                raise CommandError(
                    "Could not find a feed submitted to Amazon with "
                    "ID #{0}".format(submission_id)
                )
            if not submission:
                raise CommandError(
                    "Updating status of feeds submission failed. Aborting "
                    "further processing."
                )

            print "Updated details for feed submission #{0}".format(
                submission.submission_id
            )

            for report in feeds.process_submission_results(submission):
                print "Processed {0} messages".format(report.processed)
                print "Successful {0} messages".format(report.successful)
                print "Processed {0} messages with errors".format(
                    report.errors
                )
                print "Processed {0} messages with warnings".format(
                    report.warnings
                )

                if report.errors or report.warnings:
                    for message in report.results.all():
                        print "{0} ({1}): {2}".format(
                            message.type,
                            message.message_code,
                            message.description
                        )
                print '=' * 80
