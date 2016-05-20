define ['cs!manager', 'cs!middleware'], (ViewManager, appMiddleware) ->
  class View
    constructor: (@Q, @scopeName) ->
      @manager = ViewManager.get()
      @initMiddleware = true
      @viewCache = null
      @jsonCache = {}
      @jsonCfg = {}
      @modalNr = null
      @['__' + name] = method for name, method of appMiddleware
      @['_' + name] = method for name, method of @manager.userMiddleware

    loadAjaxView: ->
      if @initMiddleware
        @__onAjaxLoad()
        @__onLoad()
        @_onAjaxLoad() if @_onAjaxLoad
        @_onLoad() if @_onLoad
        if @jsonCfg.init_view_type
          method = @manager.getViewTypeMethod(@jsonCfg.init_view_type)
          @[method]() if @[method]
      @onAjaxLoad() if @onAjaxLoad
      @onLoad() if @onLoad

    initRequest: (viewName, urlKwargs, jsonData, callback) ->
      _urlKwargs = if @getUrlKwargs then @getUrlKwargs() else {}
      $.extend(_urlKwargs, urlKwargs)
      delete _urlKwargs[key] for key, value of _urlKwargs when not value?
      _jsonData = if @getJsonData then @getJsonData() else {}
      $.extend(_jsonData, jsonData)
      delete _jsonData[key] for key, value of _jsonData when not value?

      console.log('Debug request: ', _urlKwargs, _jsonData) if @manager.cfg.debug
      url = Urls[viewName](_urlKwargs)
      history.replaceState({}, null, url)
      $.get url, {'json_cfg': JSON.stringify(_jsonData)}, (response) ->
        callback(response)

    initView: ({viewName, urlKwargs, jsonData, animate} = {}) ->
      viewName ?= @jsonCfg.view_name
      urlKwargs ?= {}
      jsonData ?= {}
      animate ?= true
      @initRequest viewName, urlKwargs, jsonData, (response) =>
        @jsonCfg = @manager.getJsonCfg(response)
        if @jsonCfg.ajax_load
          @manager.updateView(response, animate)
          @manager.debugInfo(@jsonCfg)
          @loadAjaxView()
        else
          console.log('this should only happen if user session has expired') if @manager.cfg.debug
          location.reload()

    requestView: ({viewName, urlKwargs, jsonData, animate} = {}) ->
      viewName ?= null
      urlKwargs ?= {}
      jsonData ?= {}
      animate ?= true

      $(@manager.cfg.ajaxNode).fadeOut('fast') if animate
      if not viewName
        @initView(urlKwargs: urlKwargs, jsonData: jsonData, animate: animate)
      else
        # coffee module is required for requested view
        module = @manager.getModuleName(viewName)
        require [@manager.cfg.modulePrefix + module], (View) =>
          Q = (selector) -> $(@manager.cfg.ajaxNode).find(selector)
          view = new View(Q, @manager.cfg.ajaxNode)
          view.initView(viewName: viewName, urlKwargs: urlKwargs, jsonData: jsonData, animate: animate)

    requestSnippet: ({urlKwargs, jsonData, callback} = {}) ->
      urlKwargs ?= {}
      jsonData ?= {}
      callback ?= null

      @initRequest @jsonCfg.view_name, urlKwargs, jsonData, (response) =>
        callback(response) if callback

    requestModal: (href, jsonData = null) ->
      console.log('Debug request: ', href, jsonData) if @manager.cfg.debug
      data = {
        'modal_id': '#modal_nr' + parseInt(@modalNr + 1) or '#modal_nr1'
        'json_cfg': JSON.stringify(jsonData) if jsonData
      }
      $.get href, data, (response) =>
        $('body').append($(response).find('.modal')[0].outerHTML)
        $(data.modal_id).modal('toggle')
        jsonCfg = @manager.getJsonCfg(response)

        @manager.requireModule jsonCfg, (View) =>
          Q = (selector) -> $(data.modal_id).find(selector)
          view = new View(Q, data.modal_id)
          view.viewCache = @
          view.modalNr = @modalNr + 1 or 1
          view.jsonCfg = jsonCfg
          view.loadAjaxView()

    initModalLinks: (scope) ->
      $(scope).find('.modal-link').click (e) =>
        e.preventDefault()
        @requestModal($(e.currentTarget).attr('href'))
