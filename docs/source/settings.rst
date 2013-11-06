========
Settings
========


``MWS_ENFORCE_PARTNER_SKU``
---------------------------

default: ``True``

The seller SKU for a product used with Amazon to uniquely identify it stored on
the ``AmazonProfile`` of that product. Oscar's stock record in the *partner*
app also provides a SKU that is used with a *Partner* corresponding to a
seller/merchant ID with MWS. In most cases, you would want the partner SKU on
the ``StockRecord`` kept in sync with the *SKU* on the ``AmazonProfile``. To
enforce this constraint, you can update the stock records for Amazon-related
partners whenever the Aamzon profile is saved. This is enabled by default. To
switch it off set ``MWS_ENFORCE_PARTNER_SKU = False`` in you settings.


``MWS_ORDER_ADAPTER``
---------------------

Specify the order adapter class to use to convert an order into a fulfillment
order containing data as expected by Amazon.


``MWS_ORDER_LINE_ADAPTER``
--------------------------

The mapper class for the order line to convert it into a fulfillment orde line
including data as expected by Amazon.


``MWS_FULFILLMENT_MERCHANT_FINDER``
-----------------------------------

default: ``oscar_mws.fulfillment.finders.default_merchant_finder``


``MWS_DEFAULT_SHIPPING_SPEED``
------------------------------

default: ``Standard``
