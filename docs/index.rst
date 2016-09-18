.. django-ajax-views documentation master file, created by
   sphinx-quickstart on Fri Sep  9 16:09:03 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================
django-ajax-views
=================

This library is an extension of Django's class-based views and works together with javascript library
**require-ajax-views**. Some basic knowledge of RequireJS and Django's class-based views would be desirable
before continuing with this guide.

.. image:: _static/server_browser.svg
    :alt: server browser relations
    :width: 380
    :align: right

The idea is to create an interface between server side and client side classes that know how to communicate
with each other. This is done by creating a JS file with the same name as the **URL name** that is mapped to the
corresponding Django **view class**. RequireJS loads that file and it's class is executed automatically on request.

Client Side
-----------

Since javascript doesn't support class definitions and inheritance I recommend using coffeescript or typescript
to simply inherit from :code:`ajaxviews.View` class. You can still use javascript though by using the built in
:code:`extendjs` function to mimic class inheritance.

.. code-block:: javascript
   :caption: my_view.js
   :name: javascript class
   :linenos:

    define(['ajaxviews'], function(ajaxviews) {
      var MyView = ajaxviews.extendjs(ajaxviews.View);
      MyView.prototype.onLoad = function () {
        // access class instance variables and methods with 'this'
      };
      return MyView;
    });

.. MyView.prototype.onPageLoad = function () {
     // console.log('instance variables and methods: ', this);
     // executed on page load (init view)
   };
   MyView.prototype.onAjaxLoad = function () {
     // executed on ajax load (update view)
   };

.. container:: flex-grid

    .. code-block:: coffeescript
       :caption: my_view.coffee
       :name: coffeescript class

        define ['ajaxviews'], (ajaxviews) ->
          class MyView extends ajaxviews.View
            onLoad: ->
              # access class instance with '@'

    .. code-block:: typescript
       :caption: my_view.ts
       :name: typescript class

        define(['ajaxviews'], function(ajaxviews) {
          class MyView extends ajaxviews.View {
            onLoad() {
              // access class instance with 'this'
            }
          }
        }

.. onPageLoad: ->
     # executed on page load (init view)
   onAjaxLoad: ->
     # executed on ajax load (update view)

.. onPageLoad() {
     // executed on page load (init view)
   }
   onAjaxLoad() {
     // executed on ajax load (update view)
   }

For this to work you need to set up RequireJS and place the JS files inside the :code:`views` directory which is
located in JS root. In :code:`main.js` require :code:`ajaxviews` and initialize the app. The :code:`ajaxviews.App`
will execute the class that's placed inside the file with the same name as the *URL name* from django's *URL conf*.

.. code-block:: javascript
   :caption: main.js
   :name: main js file
   :linenos:

    // setup require config here

    require(['ajaxviews'], function(ajaxviews) {
      var App = ajaxviews.App;

      App.config({
        debug: true
      });

      App.init();
    });

Server Side
-----------

The server side :code:`ajaxviews` app provides views and mixins your views can inherit from. They take care of
passing the *URL name* the view class is mapped to, to the client side app.

.. container:: flex-grid

    .. code-block:: python
       :caption: urls.py
       :name: urls conf

        # urls.py
        from django.conf.urls import url
        from .views import MyAjaxView

        urlpatterns = [
            url(r'^my/view/$', MyAjaxView.as_view(),
                name='my_view'),
        ]

    .. code-block:: python
       :caption: views.py
       :name: view classes

        # views.py
        from django.views.generic import View
        from ajaxviews.mixins import AjaxMixin

        class MyAjaxView(AjaxMixin, View):
            pass


Make sure you include in your base html template the json config script as follows. This is important so the server
app can communicate with the client app.

.. code-block:: html

    <script id="config" type="application/json">{{ json_cfg|jsonify }}</script>

This library is still in beta. It's running already pretty stable but there is still work to do so users can override
and extend functionality.

Contents:

.. toctree::
   :maxdepth: 2


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
