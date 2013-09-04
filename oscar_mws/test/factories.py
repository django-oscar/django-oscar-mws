import factory

from django.utils.timezone import now
from django.db.models import get_model


class FeedSubmissionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'FeedSubmission')

    date_submitted = now()


class FulfillmentOrderFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('oscar_mws', 'FulfillmentOrder')

    fulfillment_id = 'extern_id_1154539615776'
    date_updated = now()
