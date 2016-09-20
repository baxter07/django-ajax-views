
********
Overview
********

.. image:: _static/server_browser.svg
    :alt: server browser relations
    :width: 380
    :align: right

The idea is to create an interface between server side and client side classes that know how to communicate
with each other. This is done by creating a JS file with the same name as the **URL name** that is mapped to the
corresponding Django **view class**. RequireJS loads that file and it's class is executed automatically on request.

Client Side
===========

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
located in JS root. In :code:`main.js` require the :code:`ajaxviews` module and initialize the app.
The :code:`ajaxviews.App` will execute the **view class** whose file name equals the **URL name** from
Django's *URL conf*.

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
===========

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
Add :code:`ajax_view = True` to the class if you have created a corresponding JS file. If not you can omit the
:code:`ajax_view` property or set it to :code:`False`. The client side **middleware** will always be executed.

The **JSON config script** is the communication channel for sites requested via URL. It should be included in
the base html template from wich all other templates inherit from.

.. code-block:: html

    <script id="config" type="application/json">{{ json_cfg|jsonify }}</script>

.. code-block:: html

    {% extends generic_template|default:'base.html' %}

.. image:: _static/template_inheritance.svg
    :alt: Template inheritance
    :width: 450
    :align: right

Templates that inherit from your base template need to extend from :code:`generic_template` so the view can be
updated automatically on ajax requests without submitting the overhead of your base html. The :code:`#ajax-content`
is the scope that's replaced when calling :code:`requestView`.

.. raw:: html

    <div class="clear"></div>
