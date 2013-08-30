import logging

from lxml import etree
from cStringIO import StringIO
from dateutil import parser as du_parser

from django.conf import settings
from django.db.models import get_model

from . import abstract_models as am
from .writers import ProductFeedWriter
from .connection import get_connection

logger = logging.getLogger('oscar_mws')

Product = get_model('catalogue', 'Product')
FeedReport = get_model("oscar_mws", "FeedReport")
FeedResult = get_model("oscar_mws", "FeedResult")
FeedSubmission = get_model("oscar_mws", "FeedSubmission")


def submit_product_feed(products, merchant_id=None, marketplace_ids=None):
    """
    Generate a product feed for the list of *products* and submit it to
    Amazon. The submission ID returned by them is used to create a
    FeedSubmission to log the progress of the submission as well as the
    products that are handled as part of the submission.
    """
    if not merchant_id:
        merchant_id = getattr(settings, "MWS_MERCHANT_ID")

    writer = ProductFeedWriter(merchant_id)

    for product in products:
        writer.add_product(product)

    optional = {}
    if marketplace_ids:
        optional['MarketplaceIdList'] = marketplace_ids

    mws_connection = get_connection()
    response = mws_connection.submit_feed(
        FeedContent=writer.as_string(),
        FeedType=am.TYPE_POST_PRODUCT_DATA,
        content_type='text/xml',
        **optional
    )

    fsinfo = response.SubmitFeedResult.FeedSubmissionInfo

    try:
        submission = FeedSubmission.objects.get(
            submission_id=fsinfo.FeedSubmissionId,
            date_submitted=du_parser.parse(fsinfo.SubmittedDate),
            feed_type=fsinfo.FeedType,
        )
    except FeedSubmission.DoesNotExist:
        submission = FeedSubmission(
            submission_id=fsinfo.FeedSubmissionId,
            date_submitted=du_parser.parse(fsinfo.SubmittedDate),
            feed_type=fsinfo.FeedType,
        )

    submission.processing_status = fsinfo.FeedProcessingStatus
    submission.save()

    return submission


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
            processing_status__in=[am.STATUS_DONE, am.STATUS_CANCELLED]
        )
    if not submissions and submission_id is not None:
        return []

    mws = get_connection()
    response = mws.get_feed_submission_list(
        FeedSubmissionIdList=[s.id for s in submissions]
    )

    if response.GetFeedSubmissionListResult.HasNext:
        #TODO: need to handle this flag
        response.GetFeedSubmissionListResult.NextToken

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


def process_submission_results(submission):
    """
    Retrieve the submission results via the MWS API to check for errors in
    the submitted feed. The report and error data is stored in a submission
    report on the submission.

    If the submission was successful, we use the Inventory API to retrieve
    generated ASINs for new products and update the stock of the products.
    """
    mws = get_connection()
    response = mws.get_feed_submission_result(FeedSubmissionId=submission.id)

    doc = etree.parse(StringIO(response))
    reports = []
    for report in doc.xpath('.//Message/ProcessingReport'):
        submission_id = int(report.find('DocumentTransactionID').text)

        if submission_id != submission.submission_id:
            logger.warning(
                'received submission result for {0} when requesting '
                '{1}'.format(submission_id, submission.submission_id)
            )
            continue

        try:
            feed_report = FeedReport.objects.get(submission=submission)
        except FeedReport.DoesNotExist:
            feed_report = FeedReport(submission=submission)

        feed_report.status_code = report.find('StatusCode').text

        summary = report.find('ProcessingSummary')
        feed_report.processed = int(summary.find('MessagesProcessed').text)
        feed_report.successful = int(summary.find('MessagesSuccessful').text)
        feed_report.errors = int(summary.find('MessagesWithError').text)
        feed_report.warnings = int(summary.find('MessagesWithWarning').text)
        feed_report.save()

        reports.append(feed_report)

        for result in report.findall('Result'):
            feed_result = FeedResult(feed_report=feed_report)
            feed_result.message_code = result.find('ResultMessageCode').text
            feed_result.description = result.find('ResultDescription').text
            feed_result.type = result.find('ResultCode').text

            product_sku = result.find('AdditionalInfo/SKU').text
            try:
                product = Product.objects.get(
                    product__stockrecord__partner_sku=product_sku
                )
            except Product.DoesNotExist:
                pass
            else:
                feed_result.product = product

            feed_result.save()

    return reports
