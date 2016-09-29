
**********
Client API
**********

.. js:class:: View

    .. js:attribute:: testme

    This is the base view class all other views extend from.

    :param dict jsonCfg: Data being passed in request and response.
    :param bool initMiddleware: Whether the middleware should be executed or not.
    :param dict utils: Helper functions loaded from ``Utils`` module.

    .. js:function:: requestView

        AJAX request to update the view. This will update the ``jsonCfg`` attribute and replace the content of
        ``.ajax-content`` that's returned by the response.

        :param str viewName: Name mapped to Django's URL conf. Default is the current view name.
        :param dict urlKwargs: Keyword arguments parsed in URL string.
        :param dict jsonData: Keyword arguments passed as additional data.
        :param bool pageLoad: If true the request won't be AJAX but via URL. Default is false.
        :param bool animate: Animate the ajax content when replaced. Default is true.

    .. js:function:: requestSnippet

        AJAX request to retrieve data or html snippets from the server.

        :param dict urlKwargs: Keyword arguments parsed in URL string.
        :param dict jsonData: Keyword arguments passed as additional data.

    .. js:function:: requestModal

        AJAX request to open a modal with the requested view.

        :param str href: URL of the view to be displayed in modal.
        :param dict jsonData: Keyword arguments passed as additional data.

.. js:data:: Middleware

    The middleware module provides functions that are hooked into the view class on every request.

    If you have not created a view class yourself it will be hooked into the base view which will be executed
    in any case.

    :returns: dictionary containing the functions listed below.

    .. js:function:: getUrlKwargs

        Parameters parsed in URL string.

        :returns: dict

    .. js:function:: getJsonData

        Parameters passed as data in ajax requests or as query strings in URL.

        :returns: dict

    .. js:function:: onPageLoad

        Executed for all pages requested via URL.

    .. js:function:: onAjaxLoad

        Executed

.. js:data:: Utils

    Built-in functions available for use in the view class.

    .. js:function:: initModalLinks

        Initialize all elements with ``.modal-link`` class to be opened in a modal.

        The element requires a ``href`` attribute that points to a view that extends from ``ModalMixin``.

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
