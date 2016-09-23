define ['cs!manager', 'cs!middleware', 'cs!utils'], (ViewManager, appMiddleware, utils) ->
  class View
    constructor: (@Q, @scopeName) ->
      @_manager = ViewManager.get()
      @initMiddleware = true
      @viewCache = null
      @jsonCache = {}
      @jsonCfg = {}
      @modalNr = null
      @utils = {}
      @utils[name] = method.bind(@) for name, method of utils
      @['__' + name] = method for name, method of appMiddleware
      @['_' + name] = method for name, method of @_manager.userMiddleware

    _loadAjaxView: ->
      if @initMiddleware
        @__onAjaxLoad()
        @__onLoad()
        @_onAjaxLoad() if @_onAjaxLoad?
        @_onLoad() if @_onLoad?
        if @jsonCfg.init_view_type
          method = @_manager.getViewTypeMethod(@jsonCfg.init_view_type)
          @[method]() if @[method]?
      @onAjaxLoad() if @onAjaxLoad?
      @onLoad() if @onLoad?

    _getRequestData: (urlKwargs, jsonData) ->
      if @__requestContext?
        _urlKwargs = if @__requestContext.getUrlKwargs? then @__requestContext.getUrlKwargs() else {}
      else
        _urlKwargs = if @getUrlKwargs? then @getUrlKwargs() else {}
      $.extend(_urlKwargs, urlKwargs)
      delete _urlKwargs[key] for key, value of _urlKwargs when not value?

      if @__requestContext?
        _jsonData = if @__requestContext.getJsonData? then @__requestContext.getJsonData() else {}
      else
        _jsonData = if @getJsonData? then @getJsonData() else {}
      $.extend(_jsonData, jsonData)
      delete _jsonData[key] for key, value of _jsonData when not value?

      return [_urlKwargs, _jsonData]

    _initRequest: (viewName, urlKwargs, jsonData, callback) ->
      [_urlKwargs, _jsonData] = @_getRequestData(urlKwargs, jsonData)
      console.log('Debug request: ', _urlKwargs, _jsonData) if @_manager.cfg.debug

      url = null
      if @modalNr
        if @Q('form[data-async]').length
          url = @Q('form[data-async]').attr('action')
        else if @jsonCfg.full_url?
          url = @jsonCfg.full_url
        else
          throw 'Modal view has no form action and no full_url specified.'
      else
        url = Urls[viewName or @jsonCfg.view_name](_urlKwargs)
        if location.hash
          if url
            url += location.hash
          else
            url = location.hash
        history.replaceState({}, null, url) if url

      url ?= location.href
      $.get url, {'json_cfg': JSON.stringify(_jsonData)}, (response) ->
        callback(response)

    _initView: (viewName, urlKwargs, jsonData, animate) ->
      viewName ?= @jsonCfg.view_name
      urlKwargs ?= {}
      jsonData ?= {}
      animate ?= true
      @_initRequest viewName, urlKwargs, jsonData, (response) =>
        @jsonCfg = @_manager.getJsonCfg(response)
        if @jsonCfg.ajax_load
          @_manager.updateView(response, animate)
          @_manager.debugInfo(@jsonCfg)
          @_loadAjaxView()
          @utils.stopProgressBar()
        else
          console.log('this should only happen if user session has expired') if @_manager.cfg.debug
          location.reload()

    requestView: ({viewName, urlKwargs, jsonData, pageLoad, animate} = {}) ->
      viewName ?= null
      urlKwargs ?= {}
      jsonData ?= {}
      pageLoad ?= false
      animate ?= true

      @utils.animateProgressBar()
      $(@_manager.cfg.html.ajaxNode).fadeOut('fast') if animate
      if not viewName
        @_initView(null, urlKwargs, jsonData, animate)
      else if pageLoad
        [_urlKwargs, _jsonData] = @_getRequestData(urlKwargs, jsonData)
        location.href = Urls[viewName](_urlKwargs) + '?json_cfg=' + JSON.stringify(_jsonData)
      else
        module = @_manager.getModuleName(viewName)
        require [@_manager.cfg.modules.prefix + module], (View) =>
          Q = (selector) -> $(@_manager.cfg.html.ajaxNode).find(selector)
          view = new View(Q, @_manager.cfg.html.ajaxNode)
          view.__requestContext = @
          view._initView(viewName, urlKwargs, jsonData, animate)
          delete view.__requestContext

    requestSnippet: ({urlKwargs, jsonData, callback} = {}) ->
      urlKwargs ?= {}
      jsonData ?= {}

      @_initRequest null, urlKwargs, jsonData, (response) =>
        callback(response)

    requestModal: (href, jsonData = null) ->
      console.log('Debug request: ', href, jsonData) if @_manager.cfg.debug
      data = {
        'modal_id': '#modal_nr' + parseInt(@modalNr + 1) or '#modal_nr1'
        'json_cfg': JSON.stringify(jsonData) if jsonData
      }
      $.get href, data, (response) =>
        $('body').append($(response).find('.modal')[0].outerHTML)
        $(data.modal_id).modal('toggle')
        jsonCfg = @_manager.getJsonCfg(response)

        @_manager.requireModule jsonCfg, (View) =>
          Q = (selector) -> $(data.modal_id).find(selector)
          view = new View(Q, data.modal_id)
          view.viewCache = @
          view.modalNr = @modalNr + 1 or 1
          view.jsonCfg = jsonCfg
          view._loadAjaxView()
