# -*- coding: utf-8 -*-
import mock
import pytest

from oscar_mws.test import factories
from oscar_mws.feeds import gateway as feed_gw
from oscar_mws.abstract_models import (
    STATUS_CANCELLED, STATUS_SUBMITTED, TYPE_POST_PRODUCT_DATA)


@pytest.fixture
def submission(transactional_db):
    submission = factories.FeedSubmissionFactory(
        submission_id='123123123',
        processing_status=STATUS_SUBMITTED)
    print submission
    return submission


def test_cancelling_submission_doesnt_updated_unchanged_status(submission):
    response = {
        'FeedSubmissionInfo': mock.Mock(
            FeedSubmissionId=submission.submission_id,
            SubmittedDate='2012-06-30',
            FeedType=submission.feed_type,
            FeedProcessingStatus=submission.processing_status)}

    with mock.patch('oscar_mws.feeds.gateway.get_merchant_connection') as conn:
        conn.return_value = mock.Mock(
            cancel_feed_submissions=mock.Mock(
                return_value=mock.Mock(parsed=response)))

        updated = feed_gw.cancel_submission(submission)

        assert updated.submission_id == submission.submission_id
        assert updated.processing_status == submission.processing_status


def test_cancelling_submission_updates_changed_status(submission):
    response = {
        'FeedSubmissionInfo': mock.Mock(
            FeedSubmissionId=submission.submission_id,
            SubmittedDate='2012-06-30',
            FeedType=submission.feed_type,
            FeedProcessingStatus=STATUS_CANCELLED)}

    with mock.patch('oscar_mws.feeds.gateway.get_merchant_connection') as conn:
        conn.return_value = mock.Mock(
            cancel_feed_submissions=mock.Mock(
                return_value=mock.Mock(parsed=response)))

        updated = feed_gw.cancel_submission(submission)

        assert updated.submission_id == submission.submission_id
        assert updated.processing_status == STATUS_CANCELLED


def test_cancelling_submission_without_db_record_creates_it(submission):
    new_submission = mock.Mock(
        submission_id='222111333',
        merchant=submission.merchant,
    )
    response = {
        'FeedSubmissionInfo': mock.Mock(
            FeedSubmissionId=new_submission.submission_id,
            SubmittedDate='2012-06-30',
            FeedType=TYPE_POST_PRODUCT_DATA,
            FeedProcessingStatus=STATUS_CANCELLED)}

    with mock.patch('oscar_mws.feeds.gateway.get_merchant_connection') as conn:
        conn.return_value = mock.Mock(
            cancel_feed_submissions=mock.Mock(
                return_value=mock.Mock(parsed=response)))

        updated = feed_gw.cancel_submission(new_submission)

        assert updated.submission_id == new_submission.submission_id
        assert updated.processing_status == STATUS_CANCELLED
