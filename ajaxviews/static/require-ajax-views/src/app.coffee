define ['cs!manager'], (ViewManager) ->
  class AjaxApp
    @_cfg =
      cfgNode: '#config'
      ajaxNode: '#ajax-content'
      modalNode: '.modal-dialog'
      viewPath: 'views/'
      mixinPath: 'mixins/'
      modulePrefix: ''
      middleware: 'middleware'
      debug: false
      mixins: {}
      progressBarAnimationSpeed: 300

    @config: (userCfg = {}) ->
      @_cfg.cfgNode = userCfg.cfgNode if userCfg.cfgNode
      @_cfg.ajaxNode = userCfg.ajaxNode if userCfg.ajaxNode
      @_cfg.modalNode = userCfg.modalNode if userCfg.modalNode?
      @_cfg.viewPath = userCfg.viewPath + '/' if userCfg.viewPath?
      @_cfg.mixinPath = userCfg.mixinPath + '/' if userCfg.mixinPath?
      @_cfg.mixins = userCfg.mixins if userCfg.mixins?
      @_cfg.modulePrefix = userCfg.modulePrefix if userCfg.modulePrefix?
      @_cfg.middleware = userCfg.middleware if userCfg.middleware?
      @_cfg.defaults = userCfg.defaults if userCfg.defaults?
      @_cfg.progressBarAnimationSpeed = userCfg.progressBarAnimationSpeed if userCfg.progressBarAnimationSpeed?
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
            view._onPageLoad() if view._onPageLoad
            view._onLoad() if view._onLoad
            if jsonCfg.init_view_type
              method = manager.getViewTypeMethod(jsonCfg.init_view_type)
              view[method]() if view[method]
          view.onPageLoad() if view.onPageLoad
          view.onLoad() if view.onLoad

      if @_cfg.middleware
        ### amdclean ###
        require [@_cfg.modulePrefix + @_cfg.middleware], (middleware) ->
          manager.userMiddleware = middleware
          loadView()
      else
        loadView()
