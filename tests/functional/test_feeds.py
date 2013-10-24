import httpretty

from django.test import TestCase
from django.db.models import get_model

from oscar_testsupport.factories import create_product

from oscar_mws.feeds import gateway
from oscar_mws import abstract_models as am

from oscar_mws.test import mixins
from oscar_mws.test import factories

FeedSubmission = get_model('oscar_mws', 'FeedSubmission')


class TestSubmittingProductFeed(mixins.DataLoaderMixin, TestCase):

    def setUp(self):
        super(TestSubmittingProductFeed, self).setUp()
        self.product = create_product()
        self.marketplace = factories.AmazonMarketplaceFactory()

    @httpretty.activate
    def test_generates_feed_submission(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://mws.amazonservices.com/',
            responses=[httpretty.Response(
                self.load_data('submit_feed_response.xml'),
            )],
        )

        submissions = gateway.submit_product_feed(
            products=[self.product],
            marketplaces=[self.marketplace],
        )
        self.assertEquals(len(submissions), 1)
        self.assertEquals(submissions[0].submission_id, '2291326430')
        self.assertEquals(
            submissions[0].processing_status,
            am.STATUS_SUBMITTED
        )


class TestUpdatingSubmissionList(mixins.DataLoaderMixin, TestCase):

    def setUp(self):
        super(TestUpdatingSubmissionList, self).setUp()
        self.merchant = factories.MerchantAccountFactory()

    @httpretty.activate
    def test_adds_feed_submissions_for_received_feeds(self):
        xml_data = self.load_data('get_feed_submission_list_response.xml')

        from xmltodict import parse
        print parse(xml_data)

        httpretty.register_uri(
            httpretty.GET,
            'https://mws.amazonservices.com/',
            body=xml_data,
        )

        submissions = gateway.update_feed_submissions(self.merchant)
        self.assertEquals(len(submissions), 1)

        submission = submissions[0]
        self.assertEquals(submission.submission_id, '2291326430')
        self.assertEquals(submission.processing_status, '_SUBMITTED_')


class TestProcessingSubmissionFeedResults(mixins.DataLoaderMixin, TestCase):

    @httpretty.activate
    def test_generates_submission_report_correctly(self):
        xml_data = self.load_data('get_feed_submission_results_response.xml')
        httpretty.register_uri(
            httpretty.GET,
            'https://mws.amazonservices.com/',
            responses=[httpretty.Response(
                xml_data,
                content_md5=self.get_md5(xml_data),
            )],
        )

        submission = factories.FeedSubmissionFactory(submission_id=7867070986)
        report = gateway.process_submission_results(submission)[0]
        self.assertEquals(
            report.submission.submission_id,
            submission.submission_id
        )
        self.assertEquals(report.processed, 1)
        self.assertEquals(report.successful, 1)
        self.assertEquals(report.errors, 0)
        self.assertEquals(report.warnings, 1)
        self.assertEquals(report.results.count(), 3)
