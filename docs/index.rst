.. django-ajax-views documentation master file, created by
   sphinx-quickstart on Fri Sep  9 16:09:03 2016.

#################
django-ajax-views
#################

This library is an extension of Django's class-based views and works together with javascript library
**require-ajax-views**.

It's main purpose is to encapsulate server/client communication to enable updating of views with a simple
function call in javascript. URL kwargs and optional parameters for incoming requests are handled as one
data set and returned as such in each response. This regulates displaying of complex views where filter
parameters are partially passed through URL when using Django's clean URL design and as hidden parameters.
Modal views and generic forms are also supported.

Some basic knowledge of Django's class-based views and RequireJS would be desirable to follow this guide.

Contents:

.. toctree::
   :maxdepth: 2

   concept
   setup

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
