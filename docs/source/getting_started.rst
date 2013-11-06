===============
Getting Started
===============

Basic Concepts
--------------

*django-oscar-mws* provides a few models that represent data retrieved from or
sent to Amazon's MWS API.

Merchant Account
~~~~~~~~~~~~~~~~

* The merchant account represents the overall account for a region such as EU,
  US.

* A merchant account has to be linked to a stock record to be able to store
  stock for a given product in the right place. A merchant has a 1-to-1
  relationship to the ``partner.Partner`` model.

* When saving a merchant account without a partner, a partner with name
  ``Amazon (<MWS_REGION>)`` is looked up or created with the merchant's
  region corresponding to ``MWS_REGION``. E.g. for a US merchant account this
  would be ``Amazon (US)``. 
