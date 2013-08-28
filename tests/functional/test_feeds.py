import httpretty

from django.test import TestCase
from django.db.models import get_model

from oscar_mws import feeds

FeedSubmission = get_model('oscar_mws', 'FeedSubmission')


FEED_SUBMISSION_LIST_RESPONSE_XML = """<?xml version="1.0"?>
<GetFeedSubmissionListResponse xmlns="http://mws.amazonservices.com/
doc/2009-01-01/">
<GetFeedSubmissionListResult>
<NextToken>2YgYW55IGNhcm5hbCBwbGVhc3VyZS4=</NextToken>
<HasNext>true</HasNext>
<FeedSubmissionInfo>
<FeedSubmissionId>2291326430</FeedSubmissionId>
<FeedType>_POST_PRODUCT_DATA_</FeedType>
<SubmittedDate>2009-02-20T02:10:35+00:00</SubmittedDate>
<FeedProcessingStatus>_SUBMITTED_</FeedProcessingStatus>
</FeedSubmissionInfo>
</GetFeedSubmissionListResult>
<ResponseMetadata>
<RequestId>1105b931-6f1c-4480-8e97-f3b467840a9e</RequestId>
</ResponseMetadata>
</GetFeedSubmissionListResponse>"""


class TestUpdatingSubmissionList(TestCase):

    def test_returns_empty_list_for_invalid_id(self):
        submissions = feeds.update_feed_submissions(submission_id=(10 ** 12))
        self.assertSequenceEqual(submissions, [])

    @httpretty.activate
    def test_adds_feed_submissions_for_received_feeds(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/',
            responses=[httpretty.Response(FEED_SUBMISSION_LIST_RESPONSE_XML)],
        )

        submissions = feeds.update_feed_submissions()
        self.assertEquals(len(submissions), 1)

        submission = submissions[0]
        self.assertEquals(submission.submission_id, '2291326430')
        self.assertEquals(submission.processing_status, '_SUBMITTED_')
