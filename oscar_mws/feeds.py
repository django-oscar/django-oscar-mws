import logging

from dateutil import parser as du_parser

from django.db.models import get_model

from .connection import get_connection
from .abstract_models import STATUS_CANCELLED, STATUS_DONE

logger = logging.getLogger('oscar_mws')

FeedSubmission = get_model("oscar_mws", "FeedSubmission")


def update_feed_submissions(submission_id=None):
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
        submission, __ = FeedSubmission.objects.get_or_create(
            submission_id=result.FeedSubmissionId,
            date_submitted=du_parser.parse(result.SubmittedDate),
            feed_type=result.FeedType,
            processing_status=result.FeedProcessingStatus,
        )
        updated_feeds.append(submission)

    return updated_feeds
