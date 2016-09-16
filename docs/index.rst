.. django-ajax-views documentation master file, created by
   sphinx-quickstart on Fri Sep  9 16:09:03 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

django-ajax-views
=================

This library is an extension of django's class based views and works together with javascript library
**require-ajax-views**.

.. image:: _static/server_browser.svg
    :alt: server browser relations
    :width: 350
    :align: right

The idea is to map the logic of django views with javascript views. This is done by creating a js file with
the same name as the url name that's mapped to the corresponding django view class. RequireJS loads that file
and executes it automatically on request.

Since javascript doesn't support class definitions and inheritance I recommend using coffeescript or typescript
to simply inherit from ajaxviews base class. You can still use plain javascript though by using extendjs and
prototypes to mimic a class and inherit it's functionality.

.. code:: javascript

    // view.js
    define(['ajaxviews'], function(ajaxviews) {
      var MyView = ajaxviews.extendjs(ajaxviews.View);
      MyView.prototype.onPageLoad = function () {
        // executed on page load (init view)
      };
      MyView.prototype.onAjaxLoad = function () {
        // executed on ajax load (update view)
      };
      MyView.prototype.onLoad = function () {
        // executed on page load and ajax load
      };
      return MyView;
    });

.. container:: flex-grid

    .. code:: coffeescript

        # view.coffee
        define ['ajaxviews'], (ajaxviews) ->
          class MyView extends ajaxviews.View
            onPageLoad: ->
              # executed on page load (init view)
            onAjaxLoad: ->
              # executed on ajax load (update view)
            onLoad: ->
              # executed on page load and ajax load

    .. code:: typescript

        // view.ts
        define(['ajaxviews'], function(ajaxviews) {
          class MyView extends ajaxviews.View {
            onPageLoad() {
              // executed on page load (init view)
            }
            onAjaxLoad() {
              // executed on ajax load (update view)
            }
            onLoad() {
              // executed on page load and ajax load
            }
          }
        }

This library is still in beta. It's running already pretty stable but there is still work to do for users to override
and extend functionality.

Contents:

.. toctree::
   :maxdepth: 2


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
