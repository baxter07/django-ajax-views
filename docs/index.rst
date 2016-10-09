.. django-ajax-views documentation master file, created by
   sphinx-quickstart on Fri Sep  9 16:09:03 2016.

#################
django-ajax-views
#################

This app is an extension of Django's
`class-based views <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_
and works together with javascript library **require-ajax-views**.

It's main purpose is to encapsulate server/client communication to enable updating of views with a simple
function call in javascript. `URL kwargs`_ and optional parameters for incoming requests are handled as one
data set and returned as such in each response. This simplifies building complex views where filter
parameters are partially passed through URL using Django's `clean URL design`_ and as hidden parameters.

Some basic knowledge of Django's
`class-based generic views <https://docs.djangoproject.com/en/dev/ref/class-based-views/flattened-index/>`_
and `RequireJS`_ would be desirable to use this app.

Features
========

- Ajax List Views
   - Ajaxable templates to update views automatically
   - Built-in generic filter support
- Generic Forms
   - Enhanced form action controls
   - Display preview to confirm actions
- Bootstrap Modals
   - Support to display form and detail views in modals

Contents
========

.. toctree::
   :maxdepth: 2

   concept
   setup
   modules/server_api
   modules/client_api

..
   contents: Generic Forms, Filter Views

   .. :source:ajaxviews/static/require-ajax-views/src/*

Indices
=======

* :ref:`genindex`
* :ref:`modindex`

..
    Release candidates
    1.2.0.dev1  # Development release
    1.2.0a1     # Alpha Release
    1.2.0b1     # Beta Release
    1.2.0rc1    # RC Release
    1.2.0       # Final Release
    1.2.0.post1 # Post Release

    Headings
    # for parts with overline
    * for chapters with overline
    = for sections
    - for subsections
    ^ for subsubsections
    " for paragraphs

    https://docs.python.org/devguide/documenting.html
    http://www.sphinx-doc.org/en/stable/markup/code.html
    http://rest-sphinx-memo.readthedocs.io/en/latest/ReST.html
    http://build-me-the-docs-please.readthedocs.io/en/latest/index.html
    http://gisellezeno.com/tutorials/sphinx-for-python-documentation.html

.. _RequireJS: http://requirejs.org

.. _URL kwargs: https://docs.djangoproject.com/en/dev/topics/http/urls/#named-groups

.. _clean URL design: https://docs.djangoproject.com/en/dev/topics/http/urls/
