define ->
  utils =
    initModalLinks: (scope) ->
      $(scope).find('.modal-link').click (e) =>
        e.preventDefault()
        @requestModal($(e.currentTarget).attr('href'))

    initDateInput: (element, opts={}) ->
      _opts = @_manager.cfg.defaults.dateWidget or {}
      $.extend(_opts, opts)
      for dateinput in $(element).toArray()
        _opts.defaultViewDate = $(dateinput).val() or '' if not _opts.defaultViewDate
        dateinput = $(dateinput).parent() if $(dateinput).parent().is('.input-group, .date')
        $(dateinput).datepicker(_opts)

    updateMultipleHiddenInput: ->
      fieldName = @Q('.drag-and-drop').data('field')
      @Q("input[type='hidden'][name='#{fieldName}']").remove()
      @Q('.selected-list li').each (index, value) ->
        $('<input>').attr({
          type: 'hidden'
          id: "id_#{fieldName}_#{index}"
          name: fieldName
          value: parseInt($(value).data('id')) || $(value).data('id')
        }).appendTo(@Q('form[data-async]'))

    initDragAndDrop: ->
      Sortable = @_manager.cfg.defaults.dragAndDrop.sortableLib
      forwardElement = @_manager.cfg.defaults.dragAndDrop.forwardElement
      backwardElement = @_manager.cfg.defaults.dragAndDrop.backwardElement

      if @Q('.drag-and-drop').length
        Sortable.create(@Q('.drag-and-drop').find('.available-list').get(0), {group: 'main', animation: 150})
        Sortable.create(@Q('.drag-and-drop').find('.selected-list').get(0), {
          group: 'main'
          animation: 150
          onSort: => @utils.updateMultipleHiddenInput()
        })
        @utils.updateMultipleHiddenInput()

        @Q('.drag-and-drop').find(forwardElement).click (e) =>
          dragRoot = $(e.currentTarget).parent().parent()
          $(dragRoot).find('.selected-list').append($(dragRoot).find('.available-list li'))
          @utils.updateMultipleHiddenInput()

        @Q('.drag-and-drop').find(backwardElement).click (e) =>
          dragRoot = $(e.currentTarget).parent().parent()
          $(dragRoot).find('.available-list').append($(dragRoot).find('.selected-list li'))
          @utils.updateMultipleHiddenInput()

    initDeleteConfirmation: ->
      if @Q('.delete-btn[data-toggle=confirmation]').length
        @Q('.delete-btn[data-toggle=confirmation]').confirmation
          popout: true
          singleton: true

    initChosenWidget: ->
      if @Q('.chosen-widget').length
        if @Q('.modal').length
          @Q('.modal').on 'shown.bs.modal', (e) =>
            @Q('.chosen-widget', $(e.currentTarget)).chosen()
        else
          @Q('.chosen-widget').chosen()

    initPagination: ->
      if @Q('.pagination').length
        @Q('.pagination').find('span').click (e) =>
          @requestView
            jsonData: {'ajax_page_nr': parseInt($(e.currentTarget).data('page'))}

    animateProgressBar: ->
      if $('#ajax-progress-bar').length
        animationSpeed = @_manager.cfg.defaults.progressBar.animationSpeed
        animateProgress = ->
          $(@).stop().width(0)
          if $(@).data('stop-animate')
            $(@).data('stop-animate', false)
          else
            $(@).animate({width: '100%'}, animationSpeed, 'swing', animateProgress)
        $('#ajax-progress-bar').slideDown('fast')
        $('#ajax-progress-bar .progress-bar').each animateProgress

    stopProgressBar: ->
      if $('#ajax-progress-bar').length
        $('#ajax-progress-bar .progress-bar').data('stop-animate', true)
        $('#ajax-progress-bar').slideUp('fast')

#if $('.popover').length
#  popover_show_event = $.fn.popover.Constructor.prototype.show
#  $.fn.popover.Constructor.prototype.show = ->
#    popover_show_event.call(this)
#    if this.options.callback
#      this.options.callback()
