.. django-ajax-views documentation master file, created by
   sphinx-quickstart on Fri Sep  9 16:09:03 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

django-ajax-views
=================

This library is an extension of django's class based views and works together with javascript library
require-ajax-views.

The idea is to map the logic of django views with javascript views. This is done by creating a js file with
the same name as the url name that's mapped to a django view class. That file contains a single class which
extends from ajaxviews base class and is executed automatically on request.

I've written the client side code with coffeescript since it supports class definitions and inheritance but
you can also use typescript or plain javascript.

This library is still in beta.

Contents:

.. toctree::
   :maxdepth: 2


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
