define ->
  class ViewManager
    _instance = null

    @get: (cfg) ->
      _instance ?= new Manager(cfg)

    class Manager
      constructor: (@cfg) ->
        @userMiddleware = {}
        throw 'View manager can not be initialized without config.' if not @cfg

      getJsonCfg: (response = null) ->
        if response
          $.parseJSON($(response).find(@cfg.cfgNode).html())
        else
          $.parseJSON($(@cfg.cfgNode).html())

      getViewTypeMethod: (viewType) ->
        switch
          when viewType == 'formView' then '_onFormLoad'
          when viewType == 'detailView' then '_onDetailLoad'
          when viewType == 'listView' then '_onListLoad'
          else null

      getModuleName: (viewName) ->
        for mixin, views of @cfg.mixins
          if viewName in views
            return @cfg.mixinPath + mixin
        return @cfg.viewPath + viewName

      requireModule: (jsonCfg, callback) ->
        @debugInfo(jsonCfg)
        if jsonCfg.ajax_view
          moduleName = @getModuleName(jsonCfg.view_name)

          viewFunc = (Module) ->
            callback(Module)

          errorFunc = (error) =>
            console.log("Debug: no module #{moduleName} defined") if @cfg.debug

          require [@cfg.modulePrefix + moduleName], viewFunc, errorFunc
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
        if animate
          $(@cfg.ajaxNode).html($(scope).find(@cfg.ajaxNode).html()).fadeIn('fast')
        else
          $(@cfg.ajaxNode).html($(scope).find(@cfg.ajaxNode).html())

      updateModal: (modalId, scope) ->
        $(modalId).find(@cfg.modalNode).replaceWith($(scope).find(@cfg.modalNode))
