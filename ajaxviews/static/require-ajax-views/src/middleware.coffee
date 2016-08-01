define ->
  middleware =
    onPageLoad: ->
      if '?' in location.href
        history.replaceState({}, null, location.href.split('?')[0])

      if @jsonCfg.preview_stage and @jsonCfg.preview_stage == 2
        preview_data = {}
        preview_data['preview_stage'] = @jsonCfg.preview_stage
        preview_model_form = @jsonCfg.preview_model_form
        if preview_model_form
          preview_data['preview_model_form'] = $(preview_model_form).formSerialize()

        $('form[data-async]').ajaxForm
          data: preview_data
          success: (response) =>
            if response.redirect?
              location.href = response.redirect
            else
              console.log('replace form?')

        $('.preview-back').click (e) =>
          e.preventDefault()
          history.back()

    onAjaxLoad: ->
      if @scopeName and @scopeName.indexOf('#modal_nr') >= 0
        modalId = @scopeName
#        ajaxData = {}
#        if @jsonCfg.preview_model_form
#          ajaxData['preview_model_form'] = $(@jsonCfg.preview_model_form).formSerialize()
#        if @jsonCfg.preview_stage
#          ajaxData['preview_stage'] = @jsonCfg.preview_stage

        @Q('form[data-async]').ajaxForm
#          data: ajaxData
          beforeSerialize: ($form, options) =>
            @onBeforeFormSerialize($form, options) if @onBeforeFormSerialize
          beforeSubmit: (arr, $form, options) =>
            @onBeforeFormSubmit(arr, $form, options) if @onBeforeFormSubmit
          success: (response) =>
            if response.success
              @jsonCache.reload_view = true
              if response.json_cache?
                @jsonCache[key] = value for key, value of response.json_cache
              $(modalId).modal('hide')
            else
              @jsonCfg = @manager.getJsonCfg(response)
              @manager.updateModal(modalId, response)
              @_loadAjaxView()

        $(modalId).find('form[data-async]').on 'click', '.popover.confirmation a[data-apply=confirmation]', (e) =>
          e.preventDefault()
          $.get $(e.currentTarget).attr('href'), {}, (response) =>
            if response.success
              @jsonCache.reload_view = true
              if response.json_cache?
                @jsonCache[key] = value for key, value of response.json_cache
              $(modalId).modal('hide')
            else
              throw 'Object deletion failed!'

        $(modalId).on 'hidden.bs.modal', (e) =>
          $(e.currentTarget).remove()
          if @viewCache.modalNr
            $('body').addClass('modal-open')

            if @jsonCache.reload_view
              @viewCache.jsonCache[key] = value for key, value of @jsonCache
              console.log('jsonCache ->', @jsonCache) if @jsonCache and @manager.cfg.debug
              subModalId = @viewCache.scopeName
              formNode = $(subModalId).find('form[data-async]')

              if $(formNode).length
                for field, pk of @jsonCache.select_choice
                  fieldNode = $(formNode).find("#id_#{field}")
                  $(fieldNode).append("""<option value="#{pk}"></option>""").trigger('chosen:updated')
                  $(fieldNode).val(pk).trigger('chosen:updated')
                data = $(formNode).formSerialize() + '&form_data=true'
                $.get $(formNode).attr('action'), data, (response) =>
                  @manager.updateModal(subModalId, response)
                  @viewCache._loadAjaxView()
              else
                $.get @viewCache.jsonCfg.full_url, {}, (response) =>
                  @manager.updateModal(subModalId, response)
                  @viewCache._loadAjaxView()
          else
            if @jsonCache.reload_view
              @viewCache.jsonCache[key] = value for key, value of @jsonCache
              console.log('jsonCache ->', @jsonCache) if @jsonCache and @manager.cfg.debug

              if @jsonCache.ajax_load
                @viewCache.onAjaxLoad() if @viewCache.onAjaxLoad
              else
                @viewCache._initView()

#        @Q('.preview-back').click (e) =>
#          e.preventDefault()
#          ajaxData = {
#            'modal_id': modalId,
#            'preview_back': true,
#            'preview_stage': 1,
#            'preview_model_form': $(@jsonCfg.preview_model_form).formSerialize()
#          }
#          $.get $(modalId).find('form[data-async]').attr('action'), ajaxData, (response) =>
#            @manager.updateCfg(response)
#            @manager.updateModal(modalId, response)
#            @manager.initView(scope: modalId)
#
#        @Q('.modal-reload').click (e) =>
#          e.preventDefault()
#          $.get $(e.currentTarget).attr('href'), {'modal_id': modalId}, (response) =>
#            @manager.initModalCfg(modalId.replace('#', '#reload'), response)
#            @manager.updateModal(modalId, response)
#            $(modalId).find('form[data-async]').append('<input type="hidden" name="modal_reload" value="true" />')
#            @manager.initView(scope: modalId)
#
#            # $(modal_id).find('[data-dismiss="modal"]').click (e) =>
#            $(modalId).find('.cancel-btn').click (e) =>
#              e.preventDefault()
#              e.stopPropagation()
#              url = $(modalId).find('form[data-async]').attr('action').replace('edit', 'detail')
#              $.get url, {'modal_reload': true}, (response) =>
#                @manager.removeModalCfg(modalId.replace('#', '#reload'))
#                @manager.updateModal(modalId, response)
#                @manager.initView(scope: modalId)

    onLoad: ->
      if @Q('.modal-link').length
        @Q('.modal-link:not(a)').on 'mouseup', (e) ->
          window.open($(this).attr('href')) if e.which == 2

        @Q('.modal-link').click (e) =>
          e.preventDefault()
          @requestModal($(e.currentTarget).attr('href'))

      if @Q('.modal-link-cfg').length
        @Q('.modal-link-cfg').click (e) =>
          e.preventDefault()
          @requestModal($(e.currentTarget).attr('href'), @jsonCfg)
