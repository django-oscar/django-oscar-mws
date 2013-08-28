import logging

from dateutil import parser as du_parser

from django.db.models import get_model

from .connection import get_connection
from .abstract_models import STATUS_CANCELLED, STATUS_DONE

logger = logging.getLogger('oscar_mws')

FeedSubmission = get_model("oscar_mws", "FeedSubmission")


def update_feed_submissions(submission_id=None):
    """
    Check the MWS API for updates on previously submitted feeds. If
    *submission_id* is specified only the feed submission matching that ID
    is requested. Otherwise, all submission that are stored in the database
    that are not _DONE_ or _CANCELLED_ are requested.

    Returns List of updated ``FeedSubmission`` instances.
    """
    if submission_id:
        submissions = FeedSubmission.objects.filter(id=submission_id)
    else:
        submissions = FeedSubmission.objects.exclude(
            processing_status__in=[STATUS_DONE, STATUS_CANCELLED]
        )
    if not submissions and submission_id is not None:
        return []

    mws = get_connection()
    response = mws.get_feed_submission_list(
        FeedSubmissionIdList=[s.id for s in submissions]
    )

    if response.GetFeedSubmissionListResult.HasNext:
        #TODO: need to handle this flag
        token = response.GetFeedSubmissionListResult.NextToken
        print token

    updated_feeds = []
    for result in response.GetFeedSubmissionListResult.FeedSubmissionInfo:
        try:
            submission = FeedSubmission.objects.get(
                submission_id=result.FeedSubmissionId,
                date_submitted=du_parser.parse(result.SubmittedDate),
                feed_type=result.FeedType,
            )
        except FeedSubmission.DoesNotExist:
            submission = FeedSubmission(
                submission_id=result.FeedSubmissionId,
                date_submitted=du_parser.parse(result.SubmittedDate),
                feed_type=result.FeedType,
            )

        if submission.processing_status != result.FeedProcessingStatus:
            updated_feeds.append(submission)

        submission.processing_status = result.FeedProcessingStatus
        submission.save()

    return updated_feeds


def process_submission_results(submission_id):
    """
    Retrieve the submission results via the MWS API to check for errors in
    the submitted feed. The report and error data is stored in a submission
    report on the submission.

    If the submission was successful, we use the Inventory API to retrieve
    generated ASINs for new products and update the stock of the products.
    """
