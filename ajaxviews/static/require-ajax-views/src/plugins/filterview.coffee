define ['cs!view'], (View) ->
  class FilterView extends View
    getJsonData: ->
      selectedFilterIndex = @jsonCfg.selected_filter_index
      sortIndex = @jsonCfg.sort_index
      {
        'selected_filter_index': selectedFilterIndex if selectedFilterIndex or selectedFilterIndex == 0
        'selected_filter_values': @jsonCfg.selected_filter_values if @jsonCfg.selected_filter_values
        'sort_index': sortIndex if sortIndex or sortIndex == 0
        'sort_order': @jsonCfg.sort_order if sortIndex or sortIndex == 0
      }

    onPageLoad: ->
      localStorage.removeItem('popover_hide_lock') if localStorage.getItem('popover_hide_lock')
      $('body').click (e) ->
        if $('.popover').length
          if not localStorage.getItem('popover_hide_lock')
            $('th[data-filter-index] > span:first-of-type').each ->
              if not $(this).is(e.target) and $(this).has(e.target).length is 0 and $('.popover').has(e.target).length is 0
                $(this).popover('hide')
          if not $('.datepicker-dropdown').length
            localStorage.removeItem('popover_hide_lock')

      if $('#default-search-form').length
        requestSearchInput = =>
          if $('#default-search-form #id_value').val()
            @requestView
              jsonData:
                'selected_filter_index': $('#default-search-form #id_value').data('filter-index')
                'selected_filter_values': $(res).text() for res in $('.yourlabs-autocomplete span')
          else
            @requestView
              jsonData:
                'selected_filter_index': null
                'selected_filter_values': null
          $('#default-search-form #id_value').val('')
          $('.yourlabs-autocomplete').remove()

        $('#default-search-form').submit ->
          requestSearchInput()
          return false

        $('#default-search-form #submit-search').click ->
          requestSearchInput()

        $('#default-search-form #id_value').yourlabsAutocomplete().input.bind 'selectChoice', (e, choice, autocomplete) ->
          location.href = Urls[$(this).data('detail-view-name')](choice.attr('data-value'))

    onAjaxLoad: ->
      filterIndex = @jsonCfg.selected_filter_index
      if filterIndex or filterIndex == 0
        $("th[data-filter-index='#{filterIndex}']").find('> span:first-of-type').css('text-decoration', 'underline')

    onLoad: ->
      @Q('.table-sort').click (e) =>
        data = {'sort_index': $(e.currentTarget).parent().data('filter-index')}
        sort_order = $(e.currentTarget).data('sort')
        if not sort_order or sort_order == 'None'
          data['sort_order'] = 'asc'
        else if sort_order == 'asc'
          data['sort_order'] = 'desc'
        else
          data = {'sort_index': null, 'sort_order': null}
        @requestView(jsonData: data)

      popover_node = 'th[data-filter-index] > span:first-of-type'
      $(popover_node).popover
        title: 'Filter Options <button type="button" class="close" aria-hidden="true">&times;</button>'
        html: true
        content: '<i>Loading ...</i>'
        placement: 'bottom'

      $(popover_node).on 'shown.bs.popover', (e) ->
        $('.popover-title button').click ->
          $(e.currentTarget).popover('hide')

      $(popover_node).on 'show.bs.popover', (e) =>
        popover = $(e.currentTarget).data('bs.popover')
        filterIndex = parseInt($(e.currentTarget).parent().data('filter-index'))
        @requestSnippet
          jsonData:
            'filter_index': filterIndex
            'ignore_selected_values': true if filterIndex != @jsonCfg.selected_filter_index
          callback: (response) =>
            scope = popover.tip().find('.popover-content')
            $(scope).html(response)

            $(scope).find('#filter_reset').click (e) =>
              @requestView
                jsonData:
                  'selected_filter_index': null
                  'selected_filter_values': []

#            if @(scope).find('hidden input with custom method name').length
#              @[customMethodName](scope, filterIndex)
            if $(scope).find('.input-daterange').length
              inputNode = $(scope).find('.input-daterange input').on 'show', ->
                localStorage.setItem('popover_hide_lock', true)

              $(inputNode).datepicker
                format: 'yyyy-mm-dd'
                autoclose: true
                calendarWeeks: true
                todayHighlight: true
                todayBtn: true
                weekStart: 1

              $(scope).find('#filter_submit').click (e) =>
                @requestView
                  jsonData:
                    'selected_filter_index': filterIndex
                    'selected_filter_values':
                      'min_date': $(scope).find('.input-daterange input:first-of-type').val()
                      'max_date': $(scope).find('.input-daterange input:last-of-type').val()
            else if $(scope).find('input[type="radio"]').length
              $(scope).find('input:radio').change (e) =>
                filterValue = $(e.currentTarget).val()
                if not filterValue or filterValue == 'all'
                  data = {
                    'selected_filter_index': null
                    'selected_filter_values': []
                  }
                else
                  data = {
                    'selected_filter_index': filterIndex
                    'selected_filter_values': filterValue
                  }
                @requestView(jsonData: data)
            else
              $(scope).find('#select-all').click (e) =>
                $(scope).find('input[type="checkbox"]').prop('checked', 'checked')
              $(scope).find('#deselect-all').click (e) =>
                $(scope).find('input[type="checkbox"]').prop('checked', false)

              $(scope).find('input[type=text]').keyup (e) =>
                if e.keyCode == 13
                  $('#filter_submit').click()
                  return
                searchString = e.currentTarget.value
                if searchString?.length
                  $(scope).find("label.checkbox:containsCaseInsensitive('#{searchString}')").fadeIn('fast')
                  $(scope).find("label.checkbox:not(:containsCaseInsensitive('#{searchString}'))").fadeOut('fast')
                else
                  $(scope).find('label.checkbox').fadeOut('fast')

              $(scope).find('#filter_submit').click (e) =>
                values_list = []
                $(scope).find('input[type="checkbox"]:checked:visible').each ->
                  values_list.push($(this).val())
                if values_list.length == 0  # or $(scope).find('input[type="checkbox"]').length == values_list.length
                  data = {
                    'selected_filter_index': null
                    'selected_filter_values': []
                  }
                else
                  data = {
                    'selected_filter_index': filterIndex
                    'selected_filter_values': values_list
                  }
                @requestView(jsonData: data)
