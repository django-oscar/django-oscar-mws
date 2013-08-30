import os
import base64
import hashlib
import httpretty

from django.test import TestCase
from django.db.models import get_model
from django.test.utils import override_settings

from oscar_mws import feeds
from oscar_mws import abstract_models as am

from oscar_mws.test import factories

FeedSubmission = get_model('oscar_mws', 'FeedSubmission')


class DataLoaderMixin(object):
    data_directory = 'tests/data'

    def get_md5(self, content):
        return base64.encodestring(hashlib.md5(content).digest()).strip()

    def get_data_directory(self):
        return os.path.join(os.getcwd(), self.data_directory)

    def load_data(self, filename):
        path = os.path.join(self.get_data_directory(), filename)
        data = None
        with open(path) as fh:
            data = fh.read()
        return data


class TestSubmittingProductFeed(DataLoaderMixin, TestCase):

    @httpretty.activate
    @override_settings(MWS_MERCHANT_ID='MERCHANT_FAKE_12345')
    def test_generates_feed_submission(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/',
            responses=[httpretty.Response(
                self.load_data('submit_feed_response.xml'),
            )],
        )

        submission = feeds.submit_product_feed([])

        self.assertEquals(submission.submission_id, '2291326430')
        self.assertEquals(submission.processing_status, am.STATUS_SUBMITTED)


class TestUpdatingSubmissionList(DataLoaderMixin, TestCase):

    def test_returns_empty_list_for_invalid_id(self):
        submissions = feeds.update_feed_submissions(submission_id=(10 ** 12))
        self.assertSequenceEqual(submissions, [])

    @httpretty.activate
    def test_adds_feed_submissions_for_received_feeds(self):
        xml_data = self.load_data('get_feed_submission_list_response.xml')

        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/',
            body=xml_data,
        )

        submissions = feeds.update_feed_submissions()
        self.assertEquals(len(submissions), 1)

        submission = submissions[0]
        self.assertEquals(submission.submission_id, '2291326430')
        self.assertEquals(submission.processing_status, '_SUBMITTED_')


class TestProcessingSubmissionFeedResults(DataLoaderMixin, TestCase):

    @httpretty.activate
    def test_generates_submission_report_correctly(self):
        xml_data = self.load_data('get_feed_submission_results_response.xml')
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/',
            responses=[httpretty.Response(
                xml_data,
                content_md5=self.get_md5(xml_data),
            )],
        )

        submission = factories.FeedSubmissionFactory(submission_id=7867070986)
        report = feeds.process_submission_results(submission)[0]
        self.assertEquals(
            report.submission.submission_id,
            submission.submission_id
        )
        self.assertEquals(report.processed, 1)
        self.assertEquals(report.successful, 1)
        self.assertEquals(report.errors, 0)
        self.assertEquals(report.warnings, 1)
        self.assertEquals(report.results.count(), 3)



