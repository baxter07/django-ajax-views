import json

from django.shortcuts import redirect
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse, QueryDict
from django.utils.html import force_text
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.forms import ValidationError

from crispy_forms.utils import render_crispy_form

from .forms import DefaultFormHelper


class AjaxMixin:
    """
    This is the core mixin that's used for all views to establish communication with the client side :class:`App`.

    It merges the optional URL parameters from the GET request with the keyword arguments retrieved from
    Django's URL conf into ``json_cfg``.

    :ivar bool ajax_view: Set to True if you have created a client side module associated with the view
        class that's inheriting from this mixin.
    :ivar dict json_cfg: Data parsed from incoming requests and returned in each response.
    """
    ajax_view = False

    def __init__(self, **kwargs):
        self.json_cfg = {}
        if not self.ajax_view:
            self.ajax_view = kwargs.pop('ajax_view', False)
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        """
        Parse incoming request parameters and assign the view name to ``json_cfg``.

        :param request: Request object
        :param args: URL positional arguments
        :param kwargs: URL keyword arguments
        :return: Call to super class
        """
        self.json_cfg.update(kwargs.copy())
        for key, value in json.loads(request.GET.dict().get('json_cfg', '{}')).items():
            if value or value is False or value == 0:
                self.json_cfg[key] = value

        if request.is_ajax():
            self.json_cfg['ajax_load'] = True

        if 'ajax_page_nr' in self.json_cfg:
            self.kwargs['page'] = self.json_cfg['ajax_page_nr']

        if self.ajax_view:
            self.json_cfg['ajax_view'] = True

        self.json_cfg['view_name'] = request.resolver_match.url_name
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Pass current view_name, page_size and stringified json_cfg on to template context.

        :param kwargs: Template context keword arguments
        :return: Modified context data from super call
        """
        context = super().get_context_data(**kwargs)
        context['view_name'] = self.json_cfg.get('view_name', None)
        if hasattr(self, 'page_size') and self.page_size:
            context['page_size'] = self.page_size
        context['json_cfg'] = mark_safe(json.dumps(
            self.json_cfg, cls=DjangoJSONEncoder
        ))
        return context


class CsrfExemptMixin:
    """
    Mixin to decorate the :func:`dispatch` method with :func:`django.views.decorators.csrf.csrf_exempt`.

    .. note:: This should always be the left-most mixin.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class FormMixin(SuccessMessageMixin):
    def __init__(self, **kwargs):
        if 'form_class' in kwargs and 'model' not in kwargs and hasattr(kwargs['form_class'].Meta, 'model'):
            kwargs['model'] = getattr(kwargs['form_class'].Meta, 'model')
        if 'form_class' in kwargs and hasattr(kwargs['form_class'].Meta, 'success_message'):
            kwargs['success_message'] = getattr(kwargs['form_class'].Meta, 'success_message')
        elif hasattr(self, 'form_class') and self.form_class and hasattr(self.form_class.Meta, 'success_message'):
            kwargs['success_message'] = getattr(self.form_class.Meta, 'success_message')
        super().__init__(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        try:
            kwargs['success_url'] = self.get_success_url()
        except:
            pass
        related_obj_ids = {}
        for key, value in self.kwargs.items():
            if '_id' in key:
                related_obj_ids[key] = value
        if related_obj_ids:
            kwargs['related_obj_ids'] = related_obj_ids
        return kwargs

    def get_extra_form_kwargs(self):
        kwargs = super().get_extra_form_kwargs()
        kwargs.update(self.get_form_kwargs())
        return kwargs

    def get_formset(self):
        formset = super().get_formset()
        formset.helper = DefaultFormHelper()
        formset.helper.form_tag = False
        return formset

    def formset_valid(self, formset):
        response = super().formset_valid(formset)
        success_message = self.get_success_message(formset.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_url(self):
        if 'success_url' in self.request.POST:
            return self.request.POST.get('success_url')
        if getattr(self, 'success_url', None):
            success_url = force_text(self.success_url)
        else:
            success_url = super().get_success_url()
        hashtag = self.request.GET.get('hashtag', None)
        if hashtag:
            success_url += '#' + hashtag
        return success_url

    def get_context_data(self, **kwargs):
        if hasattr(self, 'json_cfg') and 'init_view_type' not in self.json_cfg:
            self.json_cfg['init_view_type'] = 'formView'
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'get_form_class'):
            context['page_size'] = getattr(self.get_form_class().Meta, 'form_size', 'sm')
        return context


class ModalMixin:
    """
    *Detail* views inheriting this mixin can be displayed in a modal by calling :func:`View.requestModal`.
    """
    def dispatch(self, request, *args, **kwargs):
        self.modal_id = request.GET.get('modal_id', '').replace('#', '')
        if not self.modal_id and hasattr(self, 'json_cfg') and 'modal_id' in self.json_cfg:
            self.modal_id = self.json_cfg.get('modal_id', '').replace('#', '')
        if self.modal_id and not hasattr(self, 'form_class'):
            self.json_cfg['full_url'] = self.request.get_full_path()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.modal_id:
            # if not hasattr(self, 'form_class'):
            #     if 'json_cfg' in context:
            #         context['json_cfg']['full_url'] = self.request.get_full_path()
            #     else:
            #         context['json_cfg'] = {'full_url': self.request.get_full_path()}
            context.update({
                'modal_id': self.modal_id,
                'generic_template': 'ajaxviews/__modal_base.html',
            })
        return context


class ModalFormMixin(ModalMixin):
    """
    Used in *Update* and *Create* views to display in modals by simply calling :func:`View.requestModal` from
    the client side view class.
    """
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.modal_id:
            kwargs.update({
                'form_action': self.request.path + '?modal_id=' + self.modal_id,
                'modal_form': True
            })
        if self.request.is_ajax() and 'form_data' in self.request.GET:
            kwargs.update({
                'data': self.request.GET,
                'files': self.request.FILES,
            })
        return kwargs

    def form_valid(self, form):
        if self.modal_id:
            self.object = form.save()
            if self.request.POST.get('modal_reload', False):
                return redirect(self.get_success_url() + '?modal_id=' + self.modal_id)
            if hasattr(form, 'json_cache'):
                return JsonResponse({'success': True, 'json_cache': form.json_cache})
            return JsonResponse({'success': True})
        else:
            return super().form_valid(form)

    def render_to_response(self, context, **response_kwargs):
        # ignore validation errors on GET requests
        if 'form_data' in self.request.GET:
            context['form'].errors.clear()
        return super().render_to_response(context, **response_kwargs)


class PreviewMixin:
    """
    For usage with the default django class-based views (CreateView, UpdateView, FormView)

    Procedure:
    First display the model form.
    When submitted, execute process_preview, then display the preview form.
    If preview form submitted and valid, run done and save model form.
    Else redisplay the preview form.
    """
    preview_template_name = None
    preview_form_class = None
    _stage = 1
    _model_form = None
    _preview_back = False

    def get(self, request, *args, **kwargs):
        self._stage = int(request.GET.get('preview_stage', 1))
        self._model_form = self.get_model_form(request.GET.get('preview_model_form', None))
        self._preview_back = request.GET.get('preview_back', False)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._stage = int(request.POST.get('preview_stage', 1))
        self._model_form = self.get_model_form(request.POST.get('preview_model_form', None))
        self._preview_back = False
        return super().post(request, *args, **kwargs)

    def get_template_names(self):
        if self._stage == 2 and self.preview_template_name is not None:
            return [self.preview_template_name]
        return super().get_template_names()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not self.request.GET.get('modal_id', False):
            kwargs['form_action'] = self.request.path

        if self._stage == 2:
            kwargs['success_url'] = self.request.path
            kwargs['back_button'] = True
            kwargs['instance'] = self.get_object()
            if self._model_form:
                kwargs['model_data'] = self._model_form.cleaned_data
            else:
                kwargs['model_data'] = self._first_stage_form.cleaned_data
            kwargs.pop('delete_url', None)

            if not self._model_form:
                kwargs.pop('initial')
                kwargs.pop('prefix')
                kwargs.pop('data')
                kwargs.pop('files')

            if hasattr(self, 'success_message') and self.success_message:
                success_message = self.get_success_message(kwargs['model_data'])
                if success_message:
                    kwargs['success_message'] = success_message
        return kwargs

    def get_form_class(self):
        if not self.preview_form_class:
            raise ImproperlyConfigured('Missing preview_form_class attribute.')
        if self._stage == 2:
            return self.preview_form_class
        return self.view.form_class

    def get_form(self, form_class=None):
        if self._preview_back:
            return self._model_form
        return super().get_form(form_class)

    def get_model_form(self, form):
        if not form:
            return None
        # note that self.object is set again by get and post methods
        self.object = self.get_object()
        stage = self._stage
        self._stage = 1
        kwargs = self.get_form_kwargs()
        self._stage = stage
        kwargs.pop('data', None)
        # kwargs.pop('delete_url', None)
        form = self.form_class(QueryDict(form), **kwargs)
        if not form.is_valid():
            raise ValidationError('Model form did not validate!')
        return form

    def form_valid(self, form):
        if self._stage == 1 and form.cleaned_data.get('skip_preview', False):
            form.preview_data = {}
            return self.done(form)

        if self._stage == 2:
            model_form = self._model_form
            model_form.preview_data = form.cleaned_data
            if self.request.POST.get('success_message', None):
                messages.success(self.request, self.request.POST.get('success_message'))
            if not self.request.GET.get('modal_id', False):
                self.object = model_form.save()
                return JsonResponse({'redirect': self.get_success_url()})
            return self.done(model_form)

        self.process_preview(form)
        self._first_stage_form = form
        self._stage = 2

        preview_form = self.get_form(self.get_form_class())
        preview_form.helper.form_class = 'preview-form'

        if not self._model_form:
            self._model_form = form

        return self.render_to_response(self.get_context_data(form=preview_form))

    def get_context_data(self, **kwargs):
        self.json_cfg['preview_stage'] = self._stage
        if self._stage == 2:
            self.json_cfg['preview_model_form'] = render_crispy_form(self._model_form)
        if self._preview_back and hasattr(self.form_class.Meta, 'form_size'):
            self.json_cfg['page_size'] = getattr(self.form_class.Meta, 'form_size')
        context = super().get_context_data(**kwargs)
        # if 'json_cfg' not in context:
        #     context['json_cfg'] = {}
        # context['json_cfg']['preview_stage'] = self._stage
        if self._stage == 2:
            # Remember to pass your CSRF token to the helper method using the context dictionary if you want
            # the rendered form to be able to submit.   render_crispy_form(form, helper=None, context=None)
            # context['json_cfg']['preview_model_form'] = render_crispy_form(self._model_form)
            if hasattr(self.preview_form_class.Meta, 'headline'):
                context['headline'] = 'Preview ' + self.preview_form_class.headline
            elif hasattr(self.preview_form_class.Meta, 'headline_full'):
                context['headline'] = self.preview_form_class.headline
        # if self._preview_back and hasattr(self.form_class.Meta, 'form_size'):
        #     context['json_cfg']['page_size'] = getattr(self.form_class.Meta, 'form_size')
        if self.request.is_ajax() and self._preview_back and not self.request.GET.get('modal_id', False):
            context['generic_template'] = 'ajaxviews/__ajax_base.html'
        return context

    def get_success_url(self):
        if self._stage == 2 and not self.request.GET.get('modal_id', False):
            return self.get_object().get_absolute_url()
            # return self.request.resolver_match.url_name
        return super().get_success_url()

    def process_preview(self, form):
        pass

    def done(self, form):
        return super().form_valid(form)


# class ObjectPermMixin:
#     def dispatch(self, request, *args, **kwargs):
#         permission = None
#         for perm in get_perms_for_model(self.model):
#             if 'access_' in perm.codename:
#                 permission = self.model.__module__.split('.')[0] + '.' + perm.codename
#                 break

#         if not permission:
#             raise Exception('No access permission configured!')

#         if 'obj_perm_ids_show' in self.json_cfg:
#             for object_id in self.json_cfg['obj_perm_ids_show']:
#                 obj = self.model.objects.get(pk=object_id)
#                 if not request.user.has_perm(permission, obj):
#                     assign_perm(permission, request.user, obj)

#         if 'obj_perm_ids_hide' in self.json_cfg:
#             for object_id in self.json_cfg['obj_perm_ids_hide']:
#                 obj = self.model.objects.get(pk=object_id)
#                 if request.user.has_perm(permission, obj):
#                     remove_perm(permission, request.user, obj)
#         return super().dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if not 'obj_perm_list' in context:
#             context['obj_perm_list'] = self.model.objects.all()
#         return context
