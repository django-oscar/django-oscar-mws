========
Concepts
========

*django-oscar-mws* (OMWS) provides a few models that represent data retrieved
from or sent to Amazon's MWS API.


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


Stock Records with MWS
~~~~~~~~~~~~~~~~~~~~~~

Using MWS for fulfillment implies that we are handling physical stock that
requires shipping and the tracking of stock. Oscar's ``StockRecord`` model
provides all the necessary functionality for this. However, there is a couple
of assumptions that we have to make based on the way MWS works.


#. Stock in MWS is available on the *merchant account* level which can be
   mapped to a fulfillment region, e.g. Europe. As a result, we have to handle
   one stock record per region/seller account which is done by tying a
   ``MerchantAccount`` directly to a ``Partner``. This is automatically taken
   care of when saving a new merchant account.


#. Oscar, by default, tracks stock and uses a 2-stage approach for it. The
   amount of stock is stored in ``num_in_stock``. Whenever a customer
   successfully places an order for an item, the ``num_allocated`` on its stock
   record is incremented. The actual amount that is available to buy is
   calculated by subtracting the allocated stock from the number in stock::

    available = stockrecord.num_in_stock - stockrecord.num_allocated

   This makes tracking stock from MWS a little tricky because we can't just
   set the ``num_in_stock`` value to the supply quantity retrieved from MWS.
   This would ignore the allocated stock number and result in a wrong number of
   items available to buy. Resetting ``num_allocated`` to zero when updating
   inventory will cause issues by itself because marking an item as shipped
   will result in decrementing ``num_in_stock`` and ``num_allocated`` by the
   shipped quantity which would also result in wrong stock numbers.
   We decided for a combined solution by resetting ``num_allocated`` to zero
   when updating stock from MWS and then preventing decrementing stock when it
   is marked as shipped if the stock record is tracking MWS stock. This
   functionality is encapsulated in ``AmazonStockRecordMixin`` which you should
   add to your projects ``StockRecord``.
