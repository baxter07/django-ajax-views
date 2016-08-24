define ->
  dateutil =
    initDateInput: (element, opts) ->
      _opts = if @_defaults.bootstrapDateOptions? then @_defaults.bootstrapDateOptions else {}
      $.extend(_opts, opts)

      for dateinput in $(element).toArray()
        if not _opts.defaultViewDate
          _opts.defaultViewDate = $(dateinput).val() or ''

        if $(dateinput).parent().is('.input-group, .date')
          dateinput = $(dateinput).parent()

        $(dateinput).datepicker(_opts)
