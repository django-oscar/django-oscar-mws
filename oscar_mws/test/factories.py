import factory

from django.utils.timezone import now
from django.db.models import get_model


class FeedSubmissionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'FeedSubmission')

    date_submitted = now()
