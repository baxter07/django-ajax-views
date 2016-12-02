
.. sphinx.addnodes.desc_addname

**********
Client API
**********

Application
===========

.. class:: App

    .. .. :source: /_modules/ajaxviews/static/require-ajax-views/src/app.coffee

    This is the client side application that's initialized once the DOM is ready.

    If the JSON config script is found in the DOM, it loads the :class:`View` class with the file name that
    equals the ``view_name`` contained in the JSON config.

    The initial startup of the application executes the :func:`onPageLoad` and :func:`onLoad` functions
    of the :class:`View` class and the :class:`Middleware`.

    See configurations below:

    :ivar bool debug: Default: ``auto`` - Print request and response parameters to console. If RequireJS is found
        then debug is ``true`` otherwise ``false``. Override this behavior by setting a value manually.
    :ivar dict mixins: Default: ``{}`` - Define mixins to execute a single module for multiple views.
    :ivar str modules.prefix: Default: ``''`` - Set a prefix for all modules loaded by RequireJS_.
    :ivar str modules.viewPath: Default: ``'views/'`` - Path to view modules relative to JS root.
    :ivar str modules.mixinPath: Default: ``'mixins/'`` - Path to mixin modules relative to JS root.
    :ivar str modules.middleware: Default: ``''`` - Name and path of the middleware module relative to JS root.
    :ivar dict defaults.dateWidget: Default: ``{}`` - Global default datepicker options.
    :ivar int defaults.progressBar.animationSpeed: Default: ``300`` - Speed in milliseconds.
    :ivar object defaults.dragAndDrop.sortableLib: Default: ``null`` - Set the library_ for drag and drop support.
    :ivar str defaults.dragAndDrop.forwardElement: Default: ``'.glyphicon-forward'`` - HTML symbol to select all.
    :ivar str defaults.dragAndDrop.backwardElement: Default: ``'.glyphicon-backward'`` - HTML symbol to deselect all.

    ..
        :ivar str html.cfgNode: Default: ``'#config'`` - ID of JSON config script.
        :ivar str html.ajaxNode: Default: ``'#ajax-content'`` - ID of element that's replaced on :func:`View.requestView`.
        :ivar str html.modalNode: Default: ``'.modal-dialog'`` - Class of element that's replaced when modal is updated.
        Options to initialize date input elements.

        Args:
            my_arg (dict): argument comment.

Base View
=========

.. class:: View

    This is the base view class all other views extend from. It provides functions to update the view and
    request views to be displayed in bootstrap modals.

    Whenever a view is requested via URL the :func:`View.onPageLoad` function is executed. When
    :func:`requestView` or :func:`requestModal` is called the :func:`View.onAjaxLoad` function is executed.
    The :func:`View.onLoad` function is always executed but any of those functions can also be omitted.

    :ivar object Q: Scope of the current view. Use instead of jquery object to avoid conflicts in the DOM. On page
        load the **Q** object works the same as the jquery object itself.
    :ivar str scopeName: Name of the element defining the current scope.
    :ivar dict jsonCfg: Data returned by response.
    :ivar bool initMiddleware: Whether the middleware should be executed or not.
    :ivar dict utils: Helper functions loaded from :class:`Utils` module.
    :ivar object viewCache: When :func:`requestModal` initializes the requested view class it saves the current view
        instance to *viewCache*.
    :ivar dict jsonCache: Is used to pass data between views when a modal form is closed if changes require custom
        behavior to update the view below.
    :ivar int modalNr: If the current view is displayed in a modal it will increment the count of modals by one.

    .. function:: requestView(viewName='', urlKwargs={}, jsonData={}, pageLoad=False, animate=True)

        AJAX request to update the current view. ``urlKwargs`` are the parameters sent to the server through
        the URL string. ``jsonData`` are the keyword arguments sent to the server as hidden parameters.

        If the view class has :func:`getUrlKwargs` and/or :func:`getJsonData` functions, the parameters they return
        (as dictionaries) will also be sent to the server. The function arguments will override keyword arguments
        from :func:`getUrlKwargs` and :func:`getJsonData`.

        .. image:: /_static/request_view.svg
            :alt: request view from server

        The server side :class:`ajaxviews.views.GenericBaseView` handles the incoming request and assigns all
        parameters to the ``json_cfg`` variable of the view class.

        On request complete will update the client side ``jsonCfg`` variable and update the ``#ajax-content`` element
        that's returned by the response. The :func:`View.onAjaxLoad` and :func:`View.onLoad` functions are executed
        as last action of processing the response.

        ..
            If the :func:`View.onAjaxLoad` function has been added to the view class,
            it's executed automatically.

        :param str viewName: Name mapped to Django's URL conf. Default is the current view name.
        :param dict urlKwargs: Keyword arguments passed through URL string.
        :param dict jsonData: Keyword arguments passed as additional data in request.
        :param bool pageLoad: If True the request won't be AJAX but via URL. Used when switching between views with
            different template layouts.
        :param bool animate: Animate the ajax content when replaced.

    ..
            # request via URL
            >>> Urls[viewName](urlKwargs) + '?json_cfg=' + JSON.stringify(jsonData)
            /my/view/1/?json_cfg=<stringified json data>

    .. function:: requestSnippet(urlKwargs, jsonData, callback)

        AJAX request to retrieve data or html snippets for the current view. The request works the same as
        :func:`requestView` except that the view is not updated automatically on request complete (the *callback*
        function is executed instead).

        The usual workflow would be to catch the request in the server side ``get(request, *args, **kwargs)``
        method and return a ``JsonResponse`` or ``HttpResponse`` to update specific parts of the current view.

        :param dict urlKwargs: Keyword arguments passed through URL string.
        :param dict jsonData: Keyword arguments passed as additional data in request.
        :param object callback: Function that's called once request is complete.

    .. function:: requestModal(href, jsonData)

        Request a view via AJAX and display it in a boostrap modal.

        :param str href: URL of the view to be opend in modal.
        :param dict jsonData: Keyword arguments passed as additional data in request.

    .. function:: getUrlKwargs

        Keyword arguments used for URL reverse to parse the **URL string**.

        This function is executed whenever :func:`requestView` or :func:`requestSnippet` is called.

        :returns: dict

    .. function:: getJsonData

        Keyword arguments passed in **query string** variable ``json_cfg``. It's data is stringified so that nested
        data structures can be sent through the request as well.

        This function is executed whenever :func:`requestView` or :func:`requestSnippet` is called.

        :returns: dict

    .. function:: onPageLoad

        Executed whenever a view is requested via URL.

    .. function:: onAjaxLoad

        Executed when a view is updated by calling :func:`requestView` or when a modal is opened by
        calling :func:`requestModal`.

    .. function:: onLoad

        Executed on every request.

    .. function:: onBeforeFormSerialize(form, options)

        For form views this function will be executed before the form is serialized.

    .. function:: onBeforeFormSubmit(arr, form, options)

        For form views this function will be executed before the form is submitted.

Filter View
===========

.. class:: FilterView(View)

    This class derives from the base :class:`View` and offers filter widgets for use with
    :class:`ajaxviews.views.AjaxListView`.

Utils
=====

.. data:: Utils

    Built-in functions available for use in the :class:`View` class through the ``utils`` attribute.

    :returns: dictionary containing the functions listed below.

    .. function:: initModalLinks(scope)

        Initialize all elements with a ``.modal-link`` class to be opened in a modal.

        Those elements require a ``href`` attribute that points to a detail or form view extending from
        server side ``ajaxviews.views`` module.

        :param str scope: Element in which all modal links are initialized.

    .. function:: initDateInput(element, opts={})

        Initialize the input element using the default date widget options from the :class:`App` config.
        ``opts`` overrides the defaults.

        :param object element: Date input field.
        :param dict opts: Options to pass to the widget.

    .. function:: updateMultipleHiddenInput()

        Update hidden input elements in form views using drag and drop support for multiple select fields.

Middleware
==========

.. data:: Middleware

    The middleware module provides functions that are hooked into the view class on every request.

    If you have not created a class for the requested view, the middleware will be hooked into the base view which
    will be executed for all requests.

    :returns: dictionary containing the functions listed below.

    .. function:: onPageLoad

        Executed whenever a view is requested via URL.

    .. function:: onAjaxLoad

        Executed when a view is updated by calling :func:`View.requestView` or when a modal is opened by
        calling :func:`View.requestModal`.

    .. function:: onLoad

        Executed on every request.

    .. function:: onListLoad

        Only executed for list views.

    .. function:: onDetailLoad

        Only executed for detail views.

    .. function:: onFormLoad

        Only executed for form views.

..
    If the user doesn't specify a class for a given view the middleware will always be executed.

    :member: requestView
    :member: requestSnippet
    :member: requestModal

    """
    This is a reST style.

    :param param1: this is a first param
    :param param2: this is a second param
    :returns: this is a description of what is returned
    :raises keyError: raises an exception
    """

.. _RequireJS: http://requirejs.org

.. _library: http://rubaxa.github.io/Sortable/
