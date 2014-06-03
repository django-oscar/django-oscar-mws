===============
Getting Started
===============

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


Stock Records and MWS
~~~~~~~~~~~~~~~~~~~~~

As described in `Concepts`, integration Oscar's stock records with MWS requires
a little additional setup. Oscar assumes that it handles the allocation and
consumption of stock through the stock record(s) for a product. With MWS the
available stock is actually dictated by Amazon and can't be handled the Oscar
way. Therefore, a few extra methods on the stock record are required which are
encapsulated in the :py:class:`AmazonStockTrackingMixin
<oscar_mws.mixins.AmazonStockTrackingMixin>`.

Making these methods available to OMWS requires you to override the ``partner``
app in Oscar. Check the `documentation on how to customise Oscar apps`_ to get
a more comprehensive introduction. The short version is, you need to create
a new app in your project called ``partner`` and create a ``models.py`` module
in it. Import all the models from the core Oscar app and add the
:py:class:`AmazonStockTrackingMixin
<oscar_mws.mixins.AmazonStockTrackingMixin>` to the ``StockRecord`` model
similar to this:

.. code-block:: python

    from oscar.apps.address.abstract_models import AbstractPartnerAddress
    from oscar.apps.partner.abstract_models import *

    from oscar_mws.mixins import AmazonStockTrackingMixin


    class StockRecord(AmazonStockTrackingMixin, AbstractStockRecord):
        pass


    class Partner(AbstractPartner):
        pass


    class PartnerAddress(AbstractPartnerAddress):
        pass


    class StockAlert(AbstractStockAlert):
        pass


And then add the ``partner`` app to your ``INSTALLED_APPS`` like this:

.. code-block:: python 

    from oscar.core import get_core_apps

    INSTALLED_APPS = [
        ...
    ] + get_core_apps(['myproject.partner'])


This setup provides you with a default implementation that disables updating
the consumed stock on a MWS-enabled stock record and provides methods to update
stock from MWS when retrieved from Amazon.

.. note:: The :py:class:`AmazonStockTrackingMixin
    <oscar_mws.mixins.AmazonStockTrackingMixin>` provides a basic
    implementation for MWS-enabled stock. If you are using multiple different
    types of fulfillment partners this implementation might not be sufficient
    and you'll have to adjust the implemenation to your specific use cases.


.. _`documentation on how to customise Oscar apps`: http://django-oscar.readthedocs.org/en/latest/howto/how_to_customise_models.html



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
