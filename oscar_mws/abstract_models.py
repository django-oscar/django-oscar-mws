import oscar_mws

from collections import OrderedDict

from django.db import models
from django.conf import settings
from django.utils.timezone import now as tz_now
from django.utils.translation import ugettext_lazy as _

from lxml.builder import E

Partner = models.get_model('partner', 'Partner')
StockRecord = models.get_model('partner', 'StockRecord')


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
TYPE_POST_FULFILLMENT_ORDER_REQUEST_DATA = \
    '_POST_FULFILLMENT_ORDER_REQUEST_DATA_'
TYPE_POST_FULFILLMENT_ORDER_CANCELLATION = \
    '_POST_FULFILLMENT_ORDER_CANCELLATION'
TYPE_REQUEST_DATA = '_REQUEST_DATA'
TYPE_POST_PAYMENT_ADJUSTMENT_DATA = '_POST_PAYMENT_ADJUSTMENT_DATA_'
TYPE_POST_INVOICE_CONFIRMATION_DATA = '_POST_INVOICE_CONFIRMATION_DATA_'
TYPE_POST_STD_ACES_DATA = '_POST_STD_ACES_DATA_'
TYPE_POST_FLAT_FILE_LISTINGS_DATA = '_POST_FLAT_FILE_LISTINGS_DATA_'
TYPE_POST_FLAT_FILE_ORDER_ACKNOWLEDGEMENT_DATA = \
    '_POST_FLAT_FILE_ORDER_ACKNOWLEDGEMENT_DATA_'
TYPE_POST_FLAT_FILE_FULFILLMENT_DATA = '_POST_FLAT_FILE_FULFILLMENT_DATA_'
TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_REQUEST_DATA = \
    '_POST_FLAT_FILE_FULFILLMENT_ORDER_REQUEST_DATA_'
TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_CANCELLATION_REQUEST_DATA = \
    '_POST_FLAT_FILE_FULFILLMENT_ORDER_CANCELLATION_REQUEST_DATA_'
TYPE_POST_FLAT_FILE_FBA_CREATE_INBOUND_SHIPMENT = \
    '_POST_FLAT_FILE_FBA_CREATE_INBOUND_SHIPMENT_'
TYPE_POST_FLAT_FILE_FBA_UPDATE_INBOUND_SHIPMENT = \
    '_POST_FLAT_FILE_FBA_UPDATE_INBOUND_SHIPMENT_'
TYPE_POST_FLAT_FILE_FBA_SHIPMENT_NOTIFICATION_FEED = \
    '_POST_FLAT_FILE_FBA_SHIPMENT_NOTIFICATION_FEED_'
TYPE_POST_FLAT_FILE_FBA_CREATE_REMOVAL = \
    '_POST_FLAT_FILE_FBA_CREATE_REMOVAL_'
TYPE_POST_FLAT_FILE_PAYMENT_ADJUSTMENT_DATA = \
    '_POST_FLAT_FILE_PAYMENT_ADJUSTMENT_DATA_'
TYPE_POST_FLAT_FILE_INVOICE_CONFIRMATION_DATA = \
    '_POST_FLAT_FILE_INVOICE_CONFIRMATION_DATA_'
TYPE_POST_FLAT_FILE_INVLOADER_DATA = '_POST_FLAT_FILE_INVLOADER_DATA_'
TYPE_POST_FLAT_FILE_CONVERGENCE_LISTINGS_DATA = \
    '_POST_FLAT_FILE_CONVERGENCE_LISTINGS_DATA_'
TYPE_POST_FLAT_FILE_BOOKLOADER_DATA = '_POST_FLAT_FILE_BOOKLOADER_DATA_'
TYPE_POST_FLAT_FILE_LISTINGS_DATA = '_POST_FLAT_FILE_LISTINGS_DATA_'
TYPE_POST_FLAT_FILE_PRICEANDQUANTITYONLY = \
    '_POST_FLAT_FILE_PRICEANDQUANTITYONLY'
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
    (TYPE_POST_FULFILLMENT_ORDER_REQUEST_DATA,
     _('FBA Shipment Injection Fulfillment Feed')),
    (TYPE_POST_FULFILLMENT_ORDER_CANCELLATION, _('FBA Shipment Injection')),
    (TYPE_REQUEST_DATA, _('Cancellation Feed')),
    (TYPE_POST_PAYMENT_ADJUSTMENT_DATA, _('Order Adjustment Feed')),
    (TYPE_POST_INVOICE_CONFIRMATION_DATA, _('Invoice Confirmation Feed')),
    (TYPE_POST_STD_ACES_DATA,
     _('ACES 3.0 Data (Automotive Part Finder) Feed')),
    (TYPE_POST_FLAT_FILE_LISTINGS_DATA, _('Flat File Listings Feed')),
    (TYPE_POST_FLAT_FILE_ORDER_ACKNOWLEDGEMENT_DATA,
     _('Flat File Order Acknowledgement Feed')),
    (TYPE_POST_FLAT_FILE_FULFILLMENT_DATA,
     _('Flat File Order Fulfillment Feed')),
    (TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_REQUEST_DATA,
     _('Flat File FBA Shipment Injection Fulfillment Feed')),
    (TYPE_POST_FLAT_FILE_FULFILLMENT_ORDER_CANCELLATION_REQUEST_DATA,
     _('Flat File FBA Shipment Injection')),
    (TYPE_POST_FLAT_FILE_FBA_CREATE_INBOUND_SHIPMENT,
     _('FBA Flat File Create Inbound Shipment Feed')),
    (TYPE_POST_FLAT_FILE_FBA_UPDATE_INBOUND_SHIPMENT,
     _('FBA Flat File Update Inbound Shipment Feed')),
    (TYPE_POST_FLAT_FILE_FBA_SHIPMENT_NOTIFICATION_FEED,
     _('FBA Flat File Shipment Notification Feed')),
    (TYPE_POST_FLAT_FILE_FBA_CREATE_REMOVAL,
     _('FBA Flat File Create Removal Feed')),
    (TYPE_POST_FLAT_FILE_PAYMENT_ADJUSTMENT_DATA,
     _('Flat File Order Adjustment Feed')),
    (TYPE_POST_FLAT_FILE_INVOICE_CONFIRMATION_DATA,
     _('Flat File Invoice Confirmation Feed')),
    (TYPE_POST_FLAT_FILE_INVLOADER_DATA,
     _('Flat File Inventory Loader Feed')),
    (TYPE_POST_FLAT_FILE_CONVERGENCE_LISTINGS_DATA,
     _('Flat File Music Loader File')),
    (TYPE_POST_FLAT_FILE_BOOKLOADER_DATA, _('Flat File Book Loader File')),
    (TYPE_POST_FLAT_FILE_LISTINGS_DATA, _('Flat File Video Loader File')),
    (TYPE_POST_FLAT_FILE_PRICEANDQUANTITYONLY,
     _('Flat File Price and Quantity')),
    (TYPE_UPDATE_DATA, _('Update File')),
    (TYPE_POST_FLAT_FILE_SHOPZILLA_DATA, _('Product Ads Flat File Feed')),
    (TYPE_POST_UIEE_BOOKLOADER_DATA, _('UIEE Inventory File')),
)


class AbstractFeedSubmission(models.Model):
    """
    A feed submission represents a submitted XML feed to Amazon MWS. Updating
    product-related data such as the product details themselves, their
    inventory or price, an XML feed has to generated and submitted to MWS using
    their Feeds API. When a feed is submitted successfully, i.e. there haven't
    been any transmission error, Amazon responds with a submission ID. This ID
    can than be used to check the status of this feed.
    """
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
        _("Processing status"), max_length=200, choices=PROCESSING_STATUSES)

    merchant = models.ForeignKey(
        "MerchantAccount", verbose_name=_("Merchant account"),
        related_name="feed_submissions", null=True, blank=False)
    submitted_products = models.ManyToManyField(
        'catalogue.Product', verbose_name=_("Submitted products"),
        related_name="feed_submissions")
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
    """
    A report related to a feed submission. Whenever Amazon has finished
    processing a feed, a processing report for the feed can be retrieved from
    the API. A report is tied to a specific :class:`FeedSubmission
    <oscar.abstract_models.AbstractFeedSubmission>` ID and contains details
    about the processing status code, the nmber of processed items in the feed,
    how many of these where successful or produced errors/warnings.
    """
    submission = models.OneToOneField(
        'oscar_mws.FeedSubmission', verbose_name=_("Feed submission"),
        related_name='report')
    status_code = models.CharField(_("Status code"), max_length=100)
    processed = models.PositiveIntegerField(_("Processed messages"))
    successful = models.PositiveIntegerField(_("Successful messages"))
    errors = models.PositiveIntegerField(_("Errors"))
    warnings = models.PositiveIntegerField(_("Warnings"))

    def __unicode__(self):
        return "Report for submission #{0}".format(
            self.submission.submission_id)

    class Meta:
        abstract = True


class AbstractFeedResult(models.Model):
    """
    A feed result represents a reported warning or error for a specific item
    in a feed submission. The feed result is part of a feed report and contains
    more details about the item with an error or warning. A result is provided
    for each warning or error, so multiple results can be related to the same
    item in a feed report.
    """
    message_code = models.CharField(_("Message code"), max_length=100)
    description = models.TextField(_("Description"))
    type = models.CharField(_("Result type"), max_length=100)

    feed_report = models.ForeignKey(
        'oscar_mws.FeedReport', verbose_name=_("Feed report"),
        related_name="results")
    product = models.ForeignKey(
        'catalogue.Product', verbose_name=_("Product"),
        related_name="+", null=True, blank=True)

    class Meta:
        abstract = True


class AbstractAmazonProfile(models.Model):
    """
    An Amazon profile provides Amazon-specific attributes and settings for a
    product and connects it to Amazon maketplaces and the related merchant
    account(s). The most important (and required) attributes are the ``sku``
    and the ``marketplaces``. The ``sku`` is usually referred to in the Amazon
    MWS API as *SellerSku* and is the unique identifier used when communicating
    with MWS. If a product has no ``sku`` it cannot be used with MWS.
    The ``marketplaces`` define on wich marketplace(s) on Amazon the product
    is available and can be sold. A product can be available on one or many
    marketplaces. The marketplaces can belong to the same merchant account but
    don't have to, marketplaces themselves know what merchant account they
    belong to.
    """
    FULFILLMENT_BY_AMAZON = "AFN"
    FULFILLMENT_BY_MERCHANT = "MFN"
    FULFILLMENT_TYPES = (
        (FULFILLMENT_BY_AMAZON, _("Fulfillment by Amazon")),
        (FULFILLMENT_BY_MERCHANT, _("Fulfillment by Merchant")),
    )

    # We don't necessarily get the ASIN back right away so we need
    # to be able to create a profile without a ASIN
    asin = models.CharField(_("ASIN"), max_length=10, blank=True)
    sku = models.CharField(_("SKU"), max_length=64, db_index=True)
    product = models.OneToOneField(
        'catalogue.Product', verbose_name=_("Product"),
        related_name="amazon_profile")
    product_tax_code = models.CharField(
        _("Product tax code"), max_length=200, blank=True,
        help_text=_("Only required in Canada, Europe and Japan"))
    launch_date = models.DateTimeField(
        _("Launch date"),
        help_text=_("Controls when the products becomes searchable/browsable"),
        null=True, blank=True)
    release_date = models.DateTimeField(
        _("Release date"), null=True, blank=True,
        help_text=_("Controls when the product becomes buyable"))
    item_package_quantity = models.PositiveIntegerField(
        _("Item package quantity"), null=True, blank=True)
    number_of_items = models.PositiveIntegerField(
        _("Number of items"), null=True, blank=True)
    fulfillment_by = models.CharField(
        _("Fulfillment by"), max_length=3, choices=FULFILLMENT_TYPES,
        default=FULFILLMENT_BY_MERCHANT)
    marketplaces = models.ManyToManyField(
        'AmazonMarketplace', verbose_name=_("Marketplaces"),
        related_name="amazon_profiles")

    def get_item_type(self):
        return self.product.product_class

    def get_standard_product_id(self):
        """
        When creating a MWS feed, a product requires a ``StandardProductID`` to
        be defined. This method looks up the ID and returns the appropriate
        value. This method should be overwritten if you have a non-standard
        way of defining the standard product ID.

        By default, the ``ASIN`` of the product is return if it is available on
        the profile. Otherwise, the ``UPC`` of the related product is used and
        submitted as *UPC* type. It returns ``None`` if both strategies fail.
        The returned element is a DOM element following the structure defined
        in the MWS Feeds API, e.g. for an ASIN it returns the equivalent of::

            <StandardProductID>
                <Type>ASIN</Type>
                <Value>123124125</Value>
            </StandardProductID>

        :rtype Element: a ``ElementTree element`` representing the XML for a
            standard product ID as shown above.
        """
        if self.asin:
            return E.StandardProductID(E.Type("ASIN"), E.Value(self.asin))
        if self.product.upc and 7 < len(self.product.upc) < 16:
            return E.StandardProductID(
                E.Type("UPC"),
                E.Value(self.product.upc[:16]),
            )
        return None

    def save(self, *args, **kwargs):
        super(AbstractAmazonProfile, self).save(*args, **kwargs)
        if getattr(settings, 'MWS_ENFORCE_PARTNER_SKU', True):
            StockRecord.objects.filter(product__amazon_profile=self).update(
                partner_sku=self.sku)

    def __unicode__(self):
        return "Amazon profile for {0}".format(self.product.title)

    class Meta:
        abstract = True


class AbstractFulfillmentOrder(models.Model):
    """
    A fulfillment order corresponds to the order submitted to MWS requesting
    fulfillment by Amazon. It is related to a single Oscar order and can
    include all or a subset of the order lines in this order. The reason for
    this is due to MWS only allowing orders to a single shipping address. To
    support orders with multiple addresses, an Oscar order has to be split up
    into multiple fulfillment orders.
    """
    # Statuses for internal use only
    UNSUBMITTED = 'UNSUBMITTED'
    SUBMISSION_FAILED = 'SUBMISSION_FAILED'
    SUBMITTED = 'SUBMITTED'
    # Statuses as reported by Amazon
    RECEIVED = 'RECEIVED'
    INVALID = 'INVALID'
    PLANNING = 'PLANNING'
    PROCESSING = 'PROCESSING'
    CANCELLED = 'CANCELLED'
    COMPLETE = "COMPLETE"
    COMPLETE_PARTIALLED = "COMPLETEPARTIALLED"
    UNFULFILLABLE = 'UNFULFILLABLE'

    STATUSES = (
        (UNSUBMITTED, _("Not submitted to Amazon")),
        (SUBMISSION_FAILED, _("Failed submitting to Amazon")),
        (SUBMITTED, _("Submitted to Amazon")),
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
        _("Fulfillment ID"), max_length=32, unique=True)
    merchant = models.ForeignKey(
        "MerchantAccount", verbose_name=_("Merchant account"),
        related_name="fulfillment_orders", null=True, blank=False)

    shipping_address = models.ForeignKey(
        'order.ShippingAddress', verbose_name=_("Shipping address"),
        related_name='fulfillment_orders', null=True)
    shipping_speed = models.CharField(
        _("Shiping speed category"), max_length=200)
    comments = models.TextField(_("Comments"))

    order = models.ForeignKey(
        'order.Order', verbose_name=_("Order"),
        related_name="fulfillment_orders")
    lines = models.ManyToManyField(
        'order.Line', through='FulfillmentOrderLine', verbose_name=_("Lines"),
        related_name="fulfillment_orders")
    status = models.CharField(
        _("Fulfillment status"), max_length=25, choices=STATUSES, blank=True,
        default=UNSUBMITTED)
    date_updated = models.DateTimeField(_("Date last updated"))

    def get_items(self):
        """
        Get a list of items included in the fulfillment order corresponding to
        the ``Items`` element in the ``CreateFulfillmentOrder`` of th MWS API.
        Each item is a serialisation of the corresponding
        :class:`FulfillmentOrderLine
        <oscar_mws.abstract_models.AbstractFulfillmentOrderLine>` associated
        with this fulfillment order. It contains the query parameters used
        when submitting the fulfillment order to MWS.

        :rtype list: a list of dictionaries corresponding to the serialised
            fulfillment lines of this order.
        """
        items = []
        for line in self.lines.all().prefetch_related('fulfillment_line'):
            items.append(line.fulfillment_line.get_item_kwargs())
        return items

    def get_destination_address(self):
        """
        Get the serialised destination address as required when submitting to
        fulfillment order to MWS. The ``shipping_address`` is serialised into
        an ``OrderedDict`` with keys corresponding to the requirements in the
        ``CreateFulfillmentOrder`` API.

        :rtype OrderedDict: MWS-ready serialisation of this orders shipping
            address.
        """
        return OrderedDict(
            Name=self.shipping_address.name,
            Line1=self.shipping_address.line1,
            Line2=self.shipping_address.line2,
            line3=self.shipping_address.line3,
            City=self.shipping_address.city,
            CountryCode=self.shipping_address.country.iso_3166_1_a2,
            StateOrProvinceCode=self.shipping_address.state,
            PostalCode=self.shipping_address.postcode,
        )

    def get_order_kwargs(self):
        """
        Get the keyword arguments for this order as required by the
        :func:`submitl_fulfillment_order
        <oscar_mws.fulfillment.gateway.submit_fulfillment_order>` function.

        :rtype dict: dictionary of keyword arguments required when submitting
            the order to MWS.
        """
        kwargs = {
            'order_id': self.fulfillment_id,
            'displayable_order_id': self.fulfillment_id,
            'order_date': self.order.date_placed.isoformat(),
            'shipping_speed': self.shipping_speed,
            'comments': self.comments[:1000],
            'items': self.get_items(),
            'destination_address': self.get_destination_address(),
        }
        if self.order.user:
            kwargs['notification_emails'] = [self.order.user.email]
        return kwargs

    def save(self, *args, **kwargs):
        self.date_updated = tz_now()
        return super(AbstractFulfillmentOrder, self).save(*args, **kwargs)

    def __unicode__(self):
        return "Outbound shipment for #{0}".format(self.fulfillment_id)

    class Meta:
        abstract = True


class AbstractFulfillmentShipment(models.Model):
    """
    A shipment of all or some of the items in an order. A shipment is
    returned by MWS when requesting details about a specific fulfillment order.
    A shipment contains of one or more packages that are the physical entities
    that are shipped by Amazon. They are stored in the related
    :class:`FulfillmentShipmentPackage
    <oscar_mws.abstract_models.AbstractShipmentPackage>`.
    """
    shipment_id = models.CharField(_("Amazon shipment ID"), max_length=64)
    fulfillment_center_id = models.CharField(
        _("Fulfillment center ID"), max_length=64)
    order = models.ForeignKey(
        "order.Order", verbose_name=_("Order"),
        related_name="fulfillment_shipments")
    shipment_events = models.ManyToManyField(
        'order.ShippingEvent', verbose_name=_("Shipping events"),
        related_name="fulfillment_shipments")
    status = models.CharField(_("Shipment status"), max_length=24)
    date_estimated_arrival = models.DateTimeField(
        _("Estimated arrival"), null=True, blank=True)
    date_shipped = models.DateTimeField(_("Shipped"), null=True, blank=True)

    def __unicode__(self):
        return "Shipment {0} for order {1}",

    class Meta:
        abstract = True


class AbstractShipmentPackage(models.Model):
    """
    A shipment package is the actual package shipped by Amazon and provides
    information about the carrier and the corresponding tracking number. It is
    part of a :class:`FulfillmentShipment
    <oscar_mws.abstract_models.AbstractFulfillmentShipment>`.
    """
    package_number = models.IntegerField(_("Package number"))
    tracking_number = models.CharField(_("Tracking number"), max_length=255)
    carrier_code = models.CharField(_("Carrier code"), max_length=255)

    fulfillment_shipment = models.ForeignKey(
        'oscar_mws.FulfillmentShipment', related_name="packages",
        verbose_name=_("Fulfillment shipment"))

    def __unicode__(self):
        return "Package {0} delivered by {1}".format(
            self.tracking_number,
            self.carrier_code
        )

    class Meta:
        abstract = True


class AbstractFulfillmentOrderLine(models.Model):
    """
    A fulfillment order line corresponds to an order line in the MWS
    fulfillemnt order and relates it with the actual order line in Oscar. It
    contains the quantity submitted to Amazon, as well as a reference number
    for the item within the order (similar to the line refrence in Oscar).
    """
    line = models.OneToOneField(
        'order.Line', verbose_name=_("Line"), related_name="fulfillment_line")
    fulfillment_order = models.ForeignKey(
        'oscar_mws.FulfillmentOrder', verbose_name=_("Fulfillment order"),
        related_name="fulfillment_lines")
    order_item_id = models.CharField(
        _("Seller fulfillment order item ID"), max_length=50)

    shipment = models.ForeignKey(
        'oscar_mws.FulfillmentShipment', null=True, blank=True,
        verbose_name=_("Fulfillment shipment"), related_name="order_lines")
    package = models.ForeignKey(
        'oscar_mws.ShipmentPackage', related_name="order_lines",
        verbose_name=_("Fulfillment shipment package"), null=True, blank=True)

    quantity = models.PositiveIntegerField(_("Quantity"))
    price_incl_tax = models.DecimalField(
        _("Price incl. tax"), max_digits=12, decimal_places=2, null=True,
        blank=True)
    price_incl_tax = models.CharField(_("Currency"), max_length=3, blank=True)
    comment = models.TextField(_("Comment"), blank=True)

    def get_item_kwargs(self):
        kwargs = {
            'SellerSKU': self.line.product.amazon_profile.sku,
            'SellerFulfillmentOrderItemId': self.order_item_id,
            'Quantity': self.quantity,
        }
        if self.price_incl_tax and self.price_currency:
            kwargs['PerUnitDeclaredValue'] = OrderedDict(
                Value=self.price_incl_tax,
                CurrencyCode=self.price_currency,
            )
        if self.comment:
            kwargs['DisplayableComment'] = self.comment
        return kwargs

    @property
    def status(self):
        """
        The shipping status of this item. As long as there is no shipment
        details available from MWS, the status of the line corresponds to the
        status of the fulfillment order. Otherwise, the status of the shipment
        for this line is return.
        :rtype str: shipping status of this line.
        """
        if self.shipment:
            return self.shipment.status
        return self.fulfillment_order.status

    def __unicode__(self):
        return "Line {0} on {1}".format(
            self.line.product.amazon_profile.sku,
            self.fulfillment_order.fulfillment_id)

    class Meta:
        abstract = True


class AbstractMerchantAccount(models.Model):
    """
    A merchant account represent the merchant or seller registered with Amazon
    to use the MWS API. In general, there is a single merchant account for each
    region, e.g. US or EU. A seller can operate in multiple marketplaces within
    the given region. The merchant account and the associated region defines
    the communication endpoint with the MWS API and the ``region`` attribute
    is used to determine the appropriate API endpoint to use when sending
    requests to MWS.
    Each merchant account has their own API credentials, i.e. AWS API key and
    secret as well as the merchant/seller ID. These values have to be specified
    to be able to make requests to the MWS API. These credentials can be found
    in the seller central account for the given merchant account.

    Using Amazon MWS for fulfillment corresponds to Amazon being a fulfillment
    partner for these items. For the stock and pricing framework in Oscar to
    work correctly, a :class:`Partner <oscar.apps.partner.Partner>` is required
    that corresponds to this merchant account. A partner is automatically
    created for each new merchant account on first save. This allows for the
    merchant account to be used as fulfillment partner when specifying stock
    records for products in Oscar.
    """
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

    partner = models.OneToOneField(
        "partner.Partner", verbose_name=_("Partner"),
        related_name="amazon_merchant", null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.partner:
            self.partner, __ = Partner.objects.get_or_create(
                name="Amazon {} ({})".format(self.name, self.region)
            )
        super(AbstractMerchantAccount, self).save(*args, **kwargs)

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
