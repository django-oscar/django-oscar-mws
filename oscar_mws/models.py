from . import abstract_models as am


class FeedSubmission(am.AbstractFeedSubmission):
    pass


class FeedReport(am.AbstractFeedReport):
    pass


class FeedResult(am.AbstractFeedResult):
    pass


class AmazonProfile(am.AbstractAmazonProfile):
    pass


class FulfillmentOrder(am.AbstractFulfillmentOrder):
    pass


class FulfillmentOrderLine(am.AbstractFulfillmentOrderLine):
    pass


class FulfillmentShipment(am.AbstractFulfillmentShipment):
    pass


class ShipmentPackage(am.AbstractShipmentPackage):
    pass


class MerchantAccount(am.AbstractMerchantAccount):
    pass


class AmazonMarketplace(am.AbstractAmazonMarketplace):
    pass
