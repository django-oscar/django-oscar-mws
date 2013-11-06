=====
Notes
=====

.. warning:: For same parts of the API to work, you'll have to provide tax
    information in your MWS Pro account. Otherwise you'll get a
    ``Seller is not registered for Basic fulfillment.`` error message back.

For the time being, this is going to be a collection of finding while using the
MWS API. It mainly things that I've picked up while working on it through
feedback submitting wrong or incomplete data. It's not necessarily correct and
I am happy to be corrected where that's the case.

Fulfillment
-----------

* Fulfillment orders are created against a seller account rather than a
  marektplace. That means all marketplaces that belong to the same seller
  account are submitted against that seller account and do not require a
  marketplaces.

Submitting An Order
~~~~~~~~~~~~~~~~~~~

* The ``DestinationAddress.CountryCode`` is validated against the seller
  account region and is rejected if outside of it. E.g. a ``US`` country code
  submitted to a seller acount for Europe is rejected with::

    <Error>
      <Type>Sender</Type>
      <Code>InvalidRequestException</Code>
      <Message>Value US for parameter DestinationAddress.CountryCode is invalid. Reason: InvalidValue.</Message>
    </Error>

* Submitting an order requires a value for ``StateOrProvinceCode`` for the
  destination address. As far as I have tested it, there is no validation on
  the state for the European marketplaces. The Marketplace for the US (and most
  likely Canada as well) is rejecting anything but the official 2-letter code
  for the US state.
