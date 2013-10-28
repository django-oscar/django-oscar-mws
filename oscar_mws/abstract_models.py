import oscar_mws

from django.db import models
from django.conf import settings
from django.utils.timezone import now as tz_now
from django.utils.translation import ugettext_lazy as _

from lxml.builder import E


STATUS_DONE = "_DONE_"
STATUS_SUBMITTED = "_SUBMITTED_"
STATUS_CANCELLED = "_CANCELLED_"
STATUS_IN_PROGRESS = "_IN_PROGRESS_"
STATUS_UNCONFIRMED = "_UNCONFIRMED_"
STATUS_IN_SAFETY_NET = "_IN_SAFETY_NET_"
STATUS_AWAITING_ASYNCHRONOUS_REPLY = '_AWAITING_ASYNCHRONOUS_REPLY_'

PROCESSING_STATUSES = (
    (STATUS_DONE, _("Done")),
    (STATUS_SUBMITTED, _("Submitted")),
    (STATUS_CANCELLED, _("Cancelled")),
    (STATUS_IN_PROGRESS, _("In Progress")),
    (STATUS_UNCONFIRMED, _("Unconfirmed")),
    (STATUS_IN_SAFETY_NET, _("In Safety Net")),
    (STATUS_AWAITING_ASYNCHRONOUS_REPLY, _("Awaiting Asynchronous Reply")),
)

TYPE_POST_PRODUCT_DATA = "_POST_PRODUCT_DATA_"
TYPE_POST_PRODUCT_RELATIONSHIP_DATA = "_POST_PRODUCT_RELATIONSHIP_DATA_"
TYPE_POST_ITEM_DATA = '_POST_ITEM_DATA_'
TYPE_POST_PRODUCT_OVERRIDES_DATA = '_POST_PRODUCT_OVERRIDES_DATA_'
TYPE_POST_PRODUCT_IMAGE_DATA = '_POST_PRODUCT_IMAGE_DATA_'
TYPE_POST_PRODUCT_PRICING_DATA = '_POST_PRODUCT_PRICING_DATA_'
TYPE_POST_INVENTORY_AVAILABILITY_DATA = '_POST_INVENTORY_AVAILABILITY_DATA_'
TYPE_POST_ORDER_ACKNOWLEDGEMENT_DATA = '_POST_ORDER_ACKNOWLEDGEMENT_DATA_'
TYPE_POST_ORDER_FULFILLMENT_DATA = '_POST_ORDER_FULFILLMENT_DATA_'
TYPE_POST_FULFILLMENT_ORDER_REQUEST_DATA = '_POST_FULFILLMENT_ORDER_REQUEST_DATA_'
TYPE_POST_FULFILLMENT_ORDER_CANCELLATION = '_POST_FULFILLMENT_ORDER_CANCELLATION'
TYPE_REQUEST_DATA = '_REQUEST_DATA'
TYPE_POST_PAYMENT_ADJUSTMENT_DATA = '_POST_PAYMENT_ADJUSTMENT_DATA_'
TYPE_POST_INVOICE_CONFIRMATION_DATA = '_POST_INVOICE_CONFIRMATION_DATA_'
TYPE_POST_STD_ACES_DATA = '_POST_STD_ACES_DATA_'
TYPE_POST_FLAT_FILE_LISTINGS_DATA = '_POST_FLAT_FILE_LISTINGS_DATA_'
TYPE_POST_FLAT_FILE_ORDER_ACKNOWLEDGEMENT_DATA = '_POST_FLAT_FILE_ORDER_ACKNOWLEDGEMENT_DATA_'
TYPE_POST_FLAT_FILE_FULFILLMENT_DATA = '_POST_FLAT_FILE_FULFILLMENT_DATA_'
TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_REQUEST_DATA = '_POST_FLAT_FILE_FULFILLMENT_ORDER_REQUEST_DATA_'
TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_CANCELLATION_REQUEST_DATA = '_POST_FLAT_FILE_FULFILLMENT_ORDER_CANCELLATION_REQUEST_DATA_'
TYPE_POST_FLAT_FILE_FBA_CREATE_INBOUND_SHIPMENT = '_POST_FLAT_FILE_FBA_CREATE_INBOUND_SHIPMENT_'
TYPE_POST_FLAT_FILE_FBA_UPDATE_INBOUND_SHIPMENT = '_POST_FLAT_FILE_FBA_UPDATE_INBOUND_SHIPMENT_'
TYPE_POST_FLAT_FILE_FBA_SHIPMENT_NOTIFICATION_FEED = '_POST_FLAT_FILE_FBA_SHIPMENT_NOTIFICATION_FEED_'
TYPE_POST_FLAT_FILE_FBA_CREATE_REMOVAL = '_POST_FLAT_FILE_FBA_CREATE_REMOVAL_'
TYPE_POST_FLAT_FILE_PAYMENT_ADJUSTMENT_DATA = '_POST_FLAT_FILE_PAYMENT_ADJUSTMENT_DATA_'
TYPE_POST_FLAT_FILE_INVOICE_CONFIRMATION_DATA = '_POST_FLAT_FILE_INVOICE_CONFIRMATION_DATA_'
TYPE_POST_FLAT_FILE_INVLOADER_DATA = '_POST_FLAT_FILE_INVLOADER_DATA_'
TYPE_POST_FLAT_FILE_CONVERGENCE_LISTINGS_DATA = '_POST_FLAT_FILE_CONVERGENCE_LISTINGS_DATA_'
TYPE_POST_FLAT_FILE_BOOKLOADER_DATA = '_POST_FLAT_FILE_BOOKLOADER_DATA_'
TYPE_POST_FLAT_FILE_LISTINGS_DATA = '_POST_FLAT_FILE_LISTINGS_DATA_'
TYPE_POST_FLAT_FILE_PRICEANDQUANTITYONLY = '_POST_FLAT_FILE_PRICEANDQUANTITYONLY'
TYPE_UPDATE_DATA = '_UPDATE_DATA_'
TYPE_POST_FLAT_FILE_SHOPZILLA_DATA = '_POST_FLAT_FILE_SHOPZILLA_DATA_'
TYPE_POST_UIEE_BOOKLOADER_DATA = '_POST_UIEE_BOOKLOADER_DATA_'

FEED_TYPES = (
    (TYPE_POST_PRODUCT_DATA, _("Product Feed")),
    (TYPE_POST_PRODUCT_RELATIONSHIP_DATA, _("Relationships Feed")),
    (TYPE_POST_ITEM_DATA, _('Single Format Item Feed')),
    (TYPE_POST_PRODUCT_OVERRIDES_DATA, _('Shipping Override Feed')),
    (TYPE_POST_PRODUCT_IMAGE_DATA, _('Product Images Feed')),
    (TYPE_POST_PRODUCT_PRICING_DATA, _('Pricing Feed')),
    (TYPE_POST_INVENTORY_AVAILABILITY_DATA, _('Inventory Feed')),
    (TYPE_POST_ORDER_ACKNOWLEDGEMENT_DATA, _('Order Acknowledgement Feed')),
    (TYPE_POST_ORDER_FULFILLMENT_DATA, _('Order Fulfillment Feed')),
    (TYPE_POST_FULFILLMENT_ORDER_REQUEST_DATA, _('FBA Shipment Injection Fulfillment Feed')),
    (TYPE_POST_FULFILLMENT_ORDER_CANCELLATION, _('FBA Shipment Injection')),
    (TYPE_REQUEST_DATA, _('Cancellation Feed')),
    (TYPE_POST_PAYMENT_ADJUSTMENT_DATA, _('Order Adjustment Feed')),
    (TYPE_POST_INVOICE_CONFIRMATION_DATA, _('Invoice Confirmation Feed')),
    (TYPE_POST_STD_ACES_DATA, _('ACES 3.0 Data (Automotive Part Finder) Feed')),
    (TYPE_POST_FLAT_FILE_LISTINGS_DATA, _('Flat File Listings Feed')),
    (TYPE_POST_FLAT_FILE_ORDER_ACKNOWLEDGEMENT_DATA, _('Flat File Order Acknowledgement Feed')),
    (TYPE_POST_FLAT_FILE_FULFILLMENT_DATA, _('Flat File Order Fulfillment Feed')),
    (TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_REQUEST_DATA, _('Flat File FBA Shipment Injection Fulfillment Feed')),
    (TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_CANCELLATION_REQUEST_DATA, _('Flat File FBA Shipment Injection')),
    (TYPE_POST_FLAT_FILE_FBA_CREATE_INBOUND_SHIPMENT, _('FBA Flat File Create Inbound Shipment Feed')),
    (TYPE_POST_FLAT_FILE_FBA_UPDATE_INBOUND_SHIPMENT, _('FBA Flat File Update Inbound Shipment Feed')),
    (TYPE_POST_FLAT_FILE_FBA_SHIPMENT_NOTIFICATION_FEED, _('FBA Flat File Shipment Notification Feed')),
    (TYPE_POST_FLAT_FILE_FBA_CREATE_REMOVAL, _('FBA Flat File Create Removal Feed')),
    (TYPE_POST_FLAT_FILE_PAYMENT_ADJUSTMENT_DATA, _('Flat File Order Adjustment Feed')),
    (TYPE_POST_FLAT_FILE_INVOICE_CONFIRMATION_DATA, _('Flat File Invoice Confirmation Feed')),
    (TYPE_POST_FLAT_FILE_INVLOADER_DATA, _('Flat File Inventory Loader Feed')),
    (TYPE_POST_FLAT_FILE_CONVERGENCE_LISTINGS_DATA, _('Flat File Music Loader File')),
    (TYPE_POST_FLAT_FILE_BOOKLOADER_DATA, _('Flat File Book Loader File')),
    (TYPE_POST_FLAT_FILE_LISTINGS_DATA, _('Flat File Video Loader File')),
    (TYPE_POST_FLAT_FILE_PRICEANDQUANTITYONLY, _('Flat File Price and Quantity')),
    (TYPE_UPDATE_DATA, _('Update File')),
    (TYPE_POST_FLAT_FILE_SHOPZILLA_DATA, _('Product Ads Flat File Feed')),
    (TYPE_POST_UIEE_BOOKLOADER_DATA, _('UIEE Inventory File')),
)


class AbstractFeedSubmission(models.Model):
    submission_id = models.CharField(
        _("Submission ID"),
        max_length=64,
        unique=True,
    )
    feed_type = models.CharField(
        _("Feed type"),
        max_length=200,
        choices=FEED_TYPES,
    )
    date_created = models.DateTimeField(_("Date created"))
    date_updated = models.DateTimeField(_("Date updated"))
    date_submitted = models.DateTimeField(_("Date submitted"))
    processing_status = models.CharField(
        _("Processing status"),
        max_length=200,
        choices=PROCESSING_STATUSES
    )

    merchant = models.ForeignKey(
        "MerchantAccount",
        verbose_name=_("Merchant account"),
        related_name="feed_submissions",
        null=True, blank=False,
    )
    submitted_products = models.ManyToManyField(
        'catalogue.Product',
        verbose_name=_("Submitted products"),
        related_name="feed_submissions",
    )
    feed_xml = models.TextField(_("Submitted XML feed"), null=True, blank=True)

    def save(self, **kwargs):
        self.date_updated = tz_now()
        if not self.date_created:
            self.date_created = tz_now()
        return super(AbstractFeedSubmission, self).save(**kwargs)

    def __unicode__(self):
        return "Feed #{0}".format(self.submission_id)

    class Meta:
        abstract = True
        ordering = ['-date_updated']


class AbstractFeedReport(models.Model):
    submission = models.OneToOneField(
        'oscar_mws.FeedSubmission',
        verbose_name=_("Feed submission"),
        related_name='report',
    )
    status_code = models.CharField(_("Status code"), max_length=100)
    processed = models.PositiveIntegerField(_("Processed messages"))
    successful = models.PositiveIntegerField(_("Successful messages"))
    errors = models.PositiveIntegerField(_("Errors"))
    warnings = models.PositiveIntegerField(_("Warnings"))

    def __unicode__(self):
        return "Report for submission #{0}".format(
            self.submission.submission_id
        )

    class Meta:
        abstract = True


class AbstractFeedResult(models.Model):
    message_code = models.CharField(_("Message code"), max_length=100)
    description = models.TextField(_("Description"))
    type = models.CharField(_("Result type"), max_length=100)

    feed_report = models.ForeignKey(
        'oscar_mws.FeedReport',
        verbose_name=_("Feed report"),
        related_name="results"
    )
    product = models.ForeignKey(
        'catalogue.Product',
        verbose_name=_("Product"),
        related_name="+",
        null=True, blank=True
    )

    class Meta:
        abstract = True


class AbstractAmazonProfile(models.Model):
    SELLER_SKU_FIELD = "product__{0}".format(
        getattr(settings, "MWS_SELLER_SKU_FIELD")
    )
    FULFILLMENT_BY_AMAZON = "AFN"
    FULFILLMENT_BY_MERCHANT = "MFN"
    FULFILLMENT_TYPES = (
        (FULFILLMENT_BY_AMAZON, _("Fulfillment by Amazon")),
        (FULFILLMENT_BY_MERCHANT, _("Fulfillment by Merchant")),
    )

    # We don't necessarily get the ASIN back right away so we need
    # to be able to create a profile without a ASIN
    asin = models.CharField(_("ASIN"), max_length=10, blank=True)
    product = models.OneToOneField(
        'catalogue.Product',
        verbose_name=_("Product"),
        related_name="amazon_profile"
    )
    product_tax_code = models.CharField(
        _("Product tax code"),
        max_length=200,
        help_text=_("Only required in Canada, Europe and Japan"),
        blank=True,
    )
    launch_date = models.DateTimeField(
        _("Launch date"),
        help_text=_("Controls when the products becomes searchable/browsable"),
        null=True,
        blank=True,
    )
    release_date = models.DateTimeField(
        _("Release date"),
        help_text=_("Controls when the product becomes buyable"),
        null=True,
        blank=True,
    )
    item_package_quantity = models.PositiveIntegerField(
        _("Item package quantity"),
        null=True,
        blank=True,
    )
    number_of_items = models.PositiveIntegerField(
        _("Number of items"),
        null=True,
        blank=True,
    )
    fulfillment_by = models.CharField(
        _("Fulfillment by"),
        max_length=3,
        choices=FULFILLMENT_TYPES,
        default=FULFILLMENT_BY_MERCHANT,
    )

    marketplaces = models.ManyToManyField(
        'AmazonMarketplace',
        verbose_name=_("Marketplaces"),
        related_name="amazon_profiles",
    )

    def get_item_type(self):
        return self.product.product_class

    def get_standard_product_id(self):
        if self.asin:
            return E.StandardProductID(E.Type("ASIN"), E.Value(self.asin))
        if self.product.upc and 7 < len(self.product.upc) < 16:
            return E.StandardProductID(
                E.Type("UPC"),
                E.Value(self.product.upc[:16]),
            )
        return None

    @property
    def sku(self):
        if not hasattr(self, '_cached_sku'):
            if not self.product.has_stockrecord:
                self._cached_sku = None
            self._cached_sku = self.product.stockrecord.partner_sku.strip()
        return self._cached_sku

    def __unicode__(self):
        return "Amazon profile for {0}".format(self.product.title)

    class Meta:
        abstract = True


class AbstractFulfillmentOrder(models.Model):
    RECEIVED = 'RECEIVED'
    INVALID = 'INVALID'
    PLANNING = 'PLANNING'
    PROCESSING = 'PROCESSING'
    CANCELLED = 'CANCELLED'
    COMPLETE = "COMPLETE"
    COMPLETE_PARTIALLED = "COMPLETEPARTIALLED"
    UNFULFILLABLE = 'UNFULFILLABLE'

    STATUSES = (
        (RECEIVED, _("Received")),
        (INVALID, _("Invalid")),
        (PLANNING, _("Planning")),
        (PROCESSING, _("Processing")),
        (CANCELLED, _("Cancelled")),
        (COMPLETE, _("Complete")),
        (COMPLETE_PARTIALLED, _("Complete Partialled")),
        (UNFULFILLABLE, _("Unfullfillable")),
    )

    fulfillment_id = models.CharField(
        _("Fulfillment ID"),
        max_length=32,
        unique=True,
    )
    merchant = models.ForeignKey(
        "MerchantAccount",
        verbose_name=_("Merchant account"),
        related_name="fulfillment_orders",
        null=True, blank=False,
    )
    order = models.ForeignKey(
        'order.Order',
        verbose_name=_("Order"),
        related_name="fulfillment_orders"
    )

    lines = models.ManyToManyField(
        'order.Line',
        through='FulfillmentOrderLine',
        verbose_name=_("Lines"),
        related_name="fulfillment_orders"
    )
    status = models.CharField(
        _("Fulfillment status"),
        max_length=25,
        choices=STATUSES,
        blank=True
    )
    date_updated = models.DateTimeField(_("Date last updated"))

    def save(self, *args, **kwargs):
        self.date_updated = tz_now()
        return super(AbstractFulfillmentOrder, self).save(*args, **kwargs)

    def __unicode__(self):
        return "Outbound shipment for #{0}".format(self.fulfillment_id)

    class Meta:
        abstract = True


class AbstractFulfillmentShipment(models.Model):
    shipment_id = models.CharField(_("Amazon shipment ID"), max_length=64)
    fulfillment_center_id = models.CharField(
        _("Fulfillment center ID"),
        max_length=64
    )
    order = models.ForeignKey(
        "order.Order",
        verbose_name=_("Order"),
        related_name="fulfillment_shipments",
    )
    shipment_events = models.ManyToManyField(
        'order.ShippingEvent',
        verbose_name=_("Shipping events"),
        related_name="fulfillment_shipments",
    )
    status = models.CharField(_("Shipment status"), max_length=24)
    date_estimated_arrival = models.DateTimeField(
        _("Estimated arrival"),
        null=True, blank=True,
    )
    date_shipped = models.DateTimeField(_("Shipped"), null=True, blank=True)

    def __unicode__(self):
        return "Shipment {0} for order {1}",

    class Meta:
        abstract = True


class AbstractShipmentPackage(models.Model):
    package_number = models.IntegerField(_("Package number"))
    tracking_number = models.CharField(_("Tracking number"), max_length=255)
    carrier_code = models.CharField(_("Carrier code"), max_length=255)

    fulfillment_shipment = models.ForeignKey(
        'oscar_mws.FulfillmentShipment',
        verbose_name=_("Fulfillment shipment"),
        related_name="packages"
    )

    def __unicode__(self):
        return "Package {0} delivered by {1}".format(
            self.tracking_number,
            self.carrier_code
        )

    class Meta:
        abstract = True


class AbstractFulfillmentOrderLine(models.Model):
    line = models.OneToOneField(
        'order.Line',
        verbose_name=_("Line"),
        related_name="fulfillment_line",
    )
    fulfillment_order = models.ForeignKey(
        'oscar_mws.FulfillmentOrder',
        verbose_name=_("Fulfillment order"),
        related_name="fulfillment_lines",
    )
    order_item_id = models.CharField(
        _("Seller fulfillment order item ID"),
        max_length=50,
    )

    shipment = models.ForeignKey(
        'oscar_mws.FulfillmentShipment',
        verbose_name=_("Fulfillment shipment"),
        related_name="order_lines",
        null=True, blank=True,
    )
    package = models.ForeignKey(
        'oscar_mws.ShipmentPackage',
        verbose_name=_("Fulfillment shipment package"),
        related_name="order_lines",
        null=True, blank=True,
    )

    @property
    def status(self):
        if self.shipment:
            return self.shipment.status
        return self.fulfillment_order.status

    def __unicode__(self):
        return "Line {0} on {1}".format(
            self.line.partner_sku,
            self.fulfillment_order.fulfillment_id
        )

    class Meta:
        abstract = True


class AbstractMerchantAccount(models.Model):
    REGION_CHOICES = (
        (oscar_mws.MWS_REGION_US, _("United States (US)")),
        (oscar_mws.MWS_REGION_CA, _("Canada (CA)")),
        (oscar_mws.MWS_REGION_EU, _("Europe (EU)")),
        (oscar_mws.MWS_REGION_IN, _("India (IN)")),
        (oscar_mws.MWS_REGION_JP, _("Japan (JP)")),
        (oscar_mws.MWS_REGION_CN, _("China (CN)")),
    )
    name = models.CharField(_("Name"), max_length=200)
    region = models.CharField(
        _('Region'),
        max_length=2,
        choices=REGION_CHOICES,
        default=oscar_mws.MWS_REGION_US
    )
    aws_api_key = models.CharField(_("AWS API Key"), max_length=200)
    aws_api_secret = models.CharField(_("AWS API Secret"), max_length=200)
    seller_id = models.CharField(_("Seller/Merchant ID"), max_length=200)

    @property
    def marketplace_ids(self):
        return [m.marketplace_id for m in self.marketplaces.all()]

    def __unicode__(self):
        return "Merchant {0}".format(self.name)

    class Meta:
        abstract = True
        unique_together = (('aws_api_key', 'aws_api_secret', 'seller_id'),)


class AbstractAmazonMarketplace(models.Model):
    MARKETPLACE_CHOICES = (
        (oscar_mws.MWS_MARKETPLACE_US, _("United States (NA)")),
        (oscar_mws.MWS_MARKETPLACE_CA, _("Canada (NA)")),
        (oscar_mws.MWS_MARKETPLACE_DE, _("Germany")),
        (oscar_mws.MWS_MARKETPLACE_ES, _("Spain (EU)")),
        (oscar_mws.MWS_MARKETPLACE_FR, _("France (EU)")),
        (oscar_mws.MWS_MARKETPLACE_IN, _("India (EU)")),
        (oscar_mws.MWS_MARKETPLACE_IT, _("Italy (EU)")),
        (oscar_mws.MWS_MARKETPLACE_GB, _("Great Britain (EU)")),
        (oscar_mws.MWS_MARKETPLACE_JP, _("Japan (JP)")),
        (oscar_mws.MWS_MARKETPLACE_CN, _("China (CN)")),
    )

    name = models.CharField(_("Name"), max_length=200)
    merchant = models.ForeignKey(
        "MerchantAccount",
        verbose_name=_("Merchant account"),
        related_name="marketplaces",
    )
    region = models.CharField(
        _("Marketplace region"),
        max_length=2,
        choices=MARKETPLACE_CHOICES
    )
    marketplace_id = models.CharField(
        _("Seller marketplace ID"),
        max_length=16,
        unique=True
    )
    domain = models.CharField(_("Domain"), max_length=200, blank=True)
    currency_code = models.CharField(
        _("Currency code"),
        max_length=3,
        blank=True
    )

    @property
    def fulfillment_center_id(self):
        return oscar_mws.MWS_FULFILLMENT_CENTERS.get(self.region)

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.region)

    class Meta:
        abstract = True
