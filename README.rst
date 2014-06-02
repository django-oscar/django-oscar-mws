=======================================
Amazon MWS integration with Oscar
=======================================

.. image:: https://travis-ci.org/tangentlabs/django-oscar-mws.png?branch=master
    :target: https://travis-ci.org/tangentlabs/django-oscar-mws?branch=master

.. image:: https://coveralls.io/repos/tangentlabs/django-oscar-mws/badge.png?branch=master
    :target: https://coveralls.io/r/tangentlabs/django-oscar-mws?branch=master


Disclaimer
----------

This project is the first attempt at integrating Oscar with Amazon's MWS for 
fulfillment. Although it is currently used on a production site, it is still in
its early stages. It only integrates with a subset of features of MWS and
currently there are no plans of actively extending the coverage. Pull request
with fixes and enhancements are very welcome, though.


Documentation
-------------

The documentation of this project can be found over on the incredible
`read the docs`_: http://django-oscar-mws.rtfd.org.


Running The Tests
-----------------

We are using `pytest`_ as the test runner and testing framework for this
project. To run the test suite simple run the ``py.test`` command::

    $ py.test

In addition to test for the project itself (*unit* and *functional* tests), we
use a set of *integration* tests that use the live Amazon MWS API. These test
use a ``integration`` marker (as provided by pytest) and are disable by
default (see ``pytest.ini``). Running the integration tests requires
valid credentials for the Amazon API provided as environmental variables::

    $ export AWS_ACCESS_KEY_ID="your_mws_key"
    $ export AWS_SECRET_ACCESS_KEY="your_mws_secret"
    $ export SELLER_ID="your_seller_id"

With the credentials available, the integration test can be run using::

    $ py.test -m integration


License
-------

*django-oscar-mws* is released under the permissive `New BSD license`_.


.. _`New BSD license`: https://github.com/tangentlabs/django-oscar-mws/blob/master/LICENSE
.. _`py.test`: http://pytest.org


.. image:: https://d2weczhvl823v0.cloudfront.net/tangentlabs/django-oscar-mws/trend.png
