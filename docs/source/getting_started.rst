===============
Getting Started
===============

Basic Concepts
--------------

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


Setting Up The Sandbox
----------------------

*django-oscar-mws* comes with a sandbox site that shows how MWS can be
integrated with Oscar. It resembles a basic set up of Oscar with an
out-of-the-box integration of MWS. This section will walk you through setting
the sandbox up locally and how to make it interact with the MWS API.

.. note:: Oscar itself has quite a few dependencies and settings that might
    cause some problems when you are setting up the MWS sandbox. In addition to
    this documentation you might also want to check out the `Oscar docs on
    setting up a project`_.

The first thing to do is cloning the repository and installing it's
requirements which will includes setting up Oscar. It also creates a new
database (if it doesn't exist) creates the required tables:

.. code-block:: bash

   $ git clone git@github.com:tangentlabs/django-oscar-mws.git
   $ cd django-oscar-mws
   $ mkvirtualenv mws  # requires virtualenvwrapper to be installed
   $ make sandbox

By default, the sandbox is using Oscar's precompiled *CSS* files by setting
``USE_LESS = False``. If you want to use *LESS* to generate the CSS yourself,
take a look at the documentation on `how to use LESS with Oscar`_.

Create Admin User
~~~~~~~~~~~~~~~~~

The main interface for MWS lives in Oscar's dashboard and therefore requires an
admin user to login. Create a new admin account using Django's
``createsuperuser`` command and follow the instruction:

.. code-block:: bash

    $ ./sandbox/manage.py createsuperuser

You should now be able to run the sandbox locally using Django's builtin
HTTP server:

.. code-block:: bash

   $ ./sandbox/manage.py runserver

You now have a sample shop up and running and should be able to `navigate to
the dashboard`_ to continue the setup of your MWS credentials.


Setting Up MWS
--------------

The API endpoints provided by Amazon MWS differ based on the MWS region. The
different `regions and endpoints`_ are detailed in the Amazon docs. Each region
requires separate MWS credentials for each account. In OMWS, these accounts are
called *merchant accounts* and are used to identify the endpoints to use when
communication with MWS.

You have to create a merchant account and provide your MWS credentials to be
able to connect to MWS. Head to the *Amazon MWS > Merchants & Marketplaces* in
the Oscar dashboard and select 'Add merchant account'. A corresponding partner
account in Oscar is required for a MWS merchant account, however, if no partner
is selected explicitly, a new one will be created automatically with the same
name as the MWS merchant account.

With your merchant account(s) added, you can update the corresponding
marketplaces in the drop-down menu on the right-hand side. This will pull the
MWS marketplaces that you are able to trade in from MWS. This will also
indicate that communicating with the MWS API is successful.


.. _`navigate to the dashboard`: http://localhost:8000/dashboard/merchants/

.. _`regions and endpoints`: http://docs.developer.amazonservices.com/en_US/dev_guide/DG_Registering.html

.. _`Oscar docs on setting up a project`: http://django-oscar.readthedocs.org/en/latest/internals/sandbox.html#sample-oscar-projects

.. _`how to use LESS with Oscar`: http://django-oscar.readthedocs.org/en/latest/howto/how_to_handle_statics.html?highlight=less#less-css
