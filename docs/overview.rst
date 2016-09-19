
========
Overview
========

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
located in JS root. In :code:`main.js` require :code:`ajaxviews` and initialize the app.
The :code:`ajaxviews.App` will execute the class that's placed inside the file with the same
name as the **URL name** from Django's *URL conf*.

.. code-block:: javascript
   :caption: main.js
   :name: main js file
   :linenos:

    // setup require config here

    require(['ajaxviews'], function(ajaxviews) {
      var App = ajaxviews.App;

      App.config({
        // options
      });

      App.init();
    });

Server Side
-----------

The server side :code:`ajaxviews` app provides views and mixins your views can inherit from.

.. container:: flex-grid

    .. code-block:: python
       :caption: urls.py
       :name: urls conf

        from django.conf.urls import url
        from .views import MyAjaxView

        urlpatterns = [
            url(r'^my/view/$', MyAjaxView.as_view(),
                name='my_view'),
        ]

    .. code-block:: python
       :caption: views.py
       :name: view classes

        from django.views.generic import View
        from ajaxviews.mixins import AjaxMixin

        class MyAjaxView(AjaxMixin, View):
            ajax_view = True

The :code:`AjaxMixin` takes care of passing the **URL name** the view class is mapped to, to the client side app.
Add :code:`ajax_view = True` to the class if you have created a corresponding JS file. If :code:`ajax_view = False`
or not specified the client side **middleware** will always be executed.

Make sure to include in your base html template the json config script as follows. This is needed so the server
app can communicate with the client app.

.. code-block:: html

    <script id="config" type="application/json">{{ json_cfg|jsonify }}</script>

Also the templates that inherit from your base template need to extend from :code:`generic_template` so the
view can be updated automatically on ajax requests. Use the default tag for none ajax requests.

.. code-block:: html

    {% extends generic_template|default:'base.html' %}
