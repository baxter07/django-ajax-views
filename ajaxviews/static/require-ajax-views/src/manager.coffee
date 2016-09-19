define ->
  class ViewManager
    _instance = null

    @get: (cfg) ->
      _instance ?= new Manager(cfg)

    class Manager
      constructor: (@cfg) ->
        @userMiddleware = {}
        if not @cfg
          throw 'View manager can not be initialized without config.'

      getJsonCfg: (response = null) ->
        if response
          JSON.parse($(response).find(@cfg.html.cfgNode).html())
        else
          JSON.parse($(@cfg.html.cfgNode).html())

      getViewTypeMethod: (viewType) ->
        switch
          when viewType == 'formView' then '_onFormLoad'
          when viewType == 'detailView' then '_onDetailLoad'
          when viewType == 'listView' then '_onListLoad'
          else null

      getModuleName: (viewName) ->
        for mixin, views of @cfg.mixins
          if viewName in views
            return @cfg.modules.mixinPath + mixin
        return @cfg.modules.viewPath + viewName

      requireModule: (jsonCfg, callback) ->
        @debugInfo(jsonCfg)
        if jsonCfg.ajax_view
          moduleName = @getModuleName(jsonCfg.view_name)

          viewFunc = (Module) ->
            callback(Module)

          errorFunc = (error) =>
            console.log("Debug: no module #{moduleName} defined") if @cfg.debug

          require [@cfg.modules.prefix + moduleName], viewFunc, errorFunc
        else
          callback(require('cs!view'))

      debugInfo: (jsonCfg = {}) ->
        if @cfg.debug
          if jsonCfg.ajax_view
            console.log("Debug view:     init #{jsonCfg.view_name} view")
          else
            console.log('Debug view:     no ajax view loaded')
          console.log('Debug response:', jsonCfg)

      updateView: (scope, animate=true) ->
        node = $(@cfg.html.ajaxNode).html($(scope).find(@cfg.html.ajaxNode).html())
        node.fadeIn('fast') if animate

      updateModal: (modalId, scope) ->
        $(modalId).find(@cfg.html.modalNode).replaceWith($(scope).find(@cfg.html.modalNode))
