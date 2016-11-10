define ['cs!manager'], (ViewManager) ->
  class AjaxApp
    @_cfg =
      html:
        cfgNode: '#config'
        ajaxNode: '#ajax-content'
        modalNode: '.modal-dialog'
      modules:
        prefix: ''
        viewPath: 'views/'
        mixinPath: 'mixins/'
        middleware: ''
      mixins: {}
      debug: false
      defaults:
        progressBar:
          animationSpeed: 300
        dragAndDrop:
          sortableLib: null
          forwardElement: '.glyphicon-forward'
          backwardElement: '.glyphicon-backward'

    @config: (userCfg = {}) ->
      $.extend(@_cfg.html, userCfg.html) if userCfg.html?
      $.extend(@_cfg.modules, userCfg.modules) if userCfg.modules?
      for default_ of userCfg.defaults
        if @_cfg.defaults[default_]?
          $.extend(@_cfg.defaults[default_], userCfg.defaults[default_])
        else
          @_cfg.defaults[default_] = userCfg.defaults[default_]
      @_cfg.mixins = userCfg.mixins if userCfg.mixins?
      if userCfg.debug?
        @_cfg.debug = userCfg.debug
      else if typeof require is "function" and typeof require.specified is "function"
        @_cfg.debug = true

    @init: ->
      manager = ViewManager.get(@_cfg)
      jsonCfg = manager.getJsonCfg()

      loadView = ->
        manager.requireModule jsonCfg, (View) ->
          Q = (selector) -> $(selector)
          view = new View(Q, null)
          view.jsonCfg = jsonCfg
          if view.initMiddleware
            view.__onPageLoad()
            view.__onLoad()
            view._onPageLoad() if view._onPageLoad?
            view._onLoad() if view._onLoad?
            if jsonCfg.init_view_type
              method = manager.getViewTypeMethod(jsonCfg.init_view_type)
              view[method]() if view[method]?
          view.onPageLoad() if view.onPageLoad?
          view.onLoad() if view.onLoad?

      if @_cfg.modules.middleware
        ### amdclean ###
        require [@_cfg.modules.prefix + @_cfg.modules.middleware], (middleware) ->
          manager.userMiddleware = middleware
          loadView()
      else
        loadView()
