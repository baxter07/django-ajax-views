.. django-ajax-views documentation master file, created by
   sphinx-quickstart on Fri Sep  9 16:09:03 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================
django-ajax-views
=================

This library is an extension of Django's class-based views and works together with javascript library
**require-ajax-views**.

It's main purpose is to encapsulate server/client communication to enable updating of views with a simple
function call. URL kwargs and optional parameters for incoming requests are handled as one data set and
returned as such in each response. Modal views and generic forms are also supported.

Some basic knowledge of Django's class-based views and RequireJS would be desirable to follow this guide.

Contents:

.. toctree::
   :maxdepth: 2

   overview

..
    Indices and tables
    ------------------

    * :ref:`genindex`
    * :ref:`search`
