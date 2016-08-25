define ->
  utils =
    initModalLinks: (scope) ->
      $(scope).find('.modal-link').click (e) =>
        e.preventDefault()
        @requestModal($(e.currentTarget).attr('href'))

    initDateInput: (element, opts) ->
      _opts = @manager.cfg.defaults.dateWidget or {}
      $.extend(_opts, opts)
      for dateinput in $(element).toArray()
        _opts.defaultViewDate = $(dateinput).val() or '' if not _opts.defaultViewDate
        dateinput = $(dateinput).parent() if $(dateinput).parent().is('.input-group, .date')
        $(dateinput).datepicker(_opts)

    animateProgressBar: ->
      animationSpeed = @manager.cfg.defaults.progressBar.animationSpeed
      animateProgress = ->
        $(@).stop()
        $(@).width(0)
        if $(@).data('stop-animate')
          $(@).data('stop-animate', false)
        else
          $(@).animate({width: '100%'}, animationSpeed, 'swing', animateProgress)
      $('#ajax-progress-bar').slideDown('fast')
      $('#ajax-progress-bar .progress-bar').each animateProgress

    stopProgressBar: ->
      $('#ajax-progress-bar .progress-bar').data('stop-animate', true)
      $('#ajax-progress-bar').slideUp('fast')
