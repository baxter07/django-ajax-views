import datetime
import json

from dateutil.parser import parse

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render_to_response, redirect
from django.db.models import Min, Max
from django.utils.html import force_text
from django.utils.safestring import mark_safe
from django.contrib import messages

from .helpers import get_objects_for_model, construct_autocomplete_searchform, assign_obj_perm


class BasePlugin:
    # noinspection PyUnusedLocal
    def __init__(self, view, super_call, **kwargs):
        self._view = view
        self._init_kwargs = {}
        self._super = super_call

    @property
    def json_cfg(self):
        return self._view.json_cfg

    @json_cfg.setter
    def json_cfg(self, value):
        self._view.json_cfg = value

    @property
    def ajax_view(self):
        return self._view.ajax_view

    @property
    def request(self):
        return self._view.request

    def dispatch(self, request, *args, **kwargs):
        json_cfg = kwargs.copy()
        for key, value in json.loads(request.GET.dict().get('json_cfg', '{}')).items():
            if value or value is False or value == 0:
                json_cfg[key] = value

        if request.is_ajax():
            json_cfg['ajax_load'] = True

        if self.ajax_view:
            json_cfg['ajax_view'] = True

        json_cfg['view_name'] = request.resolver_match.url_name
        self.json_cfg.update(json_cfg)

    def get_context_data(self, context):
        context.update({
            'view_name': self.json_cfg.get('view_name', None),
            'page_size': getattr(self._view, 'page_size', None),
            'json_cfg': mark_safe(json.dumps(
                self.json_cfg, cls=DjangoJSONEncoder
            ))
        })
        return context


class ListPlugin(BasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(settings, 'DEFAULT_PAGINATE_BY'):
            self._view.paginate_by = settings.DEFAULT_PAGINATE_BY
        if hasattr(settings, 'FILTER_SEARCH_INPUT_BY'):
            self._view.filter_search_input_by = settings.FILTER_SEARCH_INPUT_BY

    @property
    def model(self):
        return self._view.model

    @property
    def paginate_by(self):
        return self._view.paginate_by

    @property
    def filter_fields(self):
        return self._view.filter_fields if hasattr(self._view, 'filter_fields') else None

    @property
    def filter_user(self):
        return self._view.filter_user if hasattr(self._view, 'filter_user') else None

    @property
    def filter_search_input_by(self):
        return self._view.filter_search_input_by if hasattr(self._view, 'filter_search_input_by') else None

    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        if 'ajax_page_nr' in self.json_cfg:
            self._view.kwargs['page'] = self.json_cfg['ajax_page_nr']

    # noinspection PyUnusedLocal
    def get(self, request, *args, **kwargs):
        self.json_cfg['init_view_type'] = 'listView'
        if self.json_cfg.get('filter_index', -1) >= 0:
            filter_field = self.filter_fields[int(self.json_cfg['filter_index'])]
            if isinstance(filter_field, str):
                filter_values = self._get_queryset_all().get_unique_values(filter_field)
                values_list = []
                for value in filter_values:
                    if value:
                        values_list.append((value, value))
                return self._multiple_filter_response(values_list)
            elif isinstance(filter_field, tuple):
                if len(filter_field) == 2 and filter_field[1] == 'date':
                    return self._date_filter_response(filter_field[0])
                elif len(filter_field) == 3 and (filter_field[1] == 'dict' or filter_field[1] == 'set'):
                    filter_values = self._get_queryset_all().get_unique_values(filter_field[0])
                    values_list = [(value, dict(filter_field[2])[value]) for value in filter_values if value]
                    return self._multiple_filter_response(values_list)
                else:
                    raise LookupError('Invalid filter set!')
            else:
                raise LookupError('Invalid filter field!')

    def get_queryset(self, **kwargs):
        if getattr(self._view, 'filter_user', False):
            queryset = get_objects_for_model(self.request.user, self.model)
        else:
            queryset = self._super.get_queryset()
        if hasattr(queryset, 'default_filter'):
            opts = self.json_cfg.copy()
            if hasattr(self, 'filter_fields'):
                if self.json_cfg.get('selected_filter_index', -1) >= 0:
                    opts['filter_field'] = self.filter_fields[int(self.json_cfg['selected_filter_index'])]
                if self.json_cfg.get('sort_index', -1) >= 0:
                    opts['sort_field'] = self.filter_fields[int(self.json_cfg['sort_index'])]
            return queryset.default_filter(opts, **kwargs)
        return queryset

    def get_context_data(self, context):
        context = super().get_context_data(context)
        if self.request.is_ajax() and not self.request.GET.get('modal_id', False):
            context['generic_template'] = 'ajaxviews/__ajax_base.html'
        if not self.request.is_ajax() and hasattr(self, 'search_field'):
            context['search_form'] = construct_autocomplete_searchform(self.search_field)
        if self.json_cfg.get('sort_index', -1) >= 0:
            context['sort_index'] = self.json_cfg['sort_index']
            context['sort_order'] = self.json_cfg.get('sort_order', None)
        return context

    def _get_queryset_all(self):
        if getattr(self._view, 'filter_user', False):
            return get_objects_for_model(self.request.user, self.model)
        return self.model.objects.all()

    def _multiple_filter_response(self, values_list):
        selected_values = []
        if not self.json_cfg.get('ignore_selected_values', False):
            selected_values = self.json_cfg.get('selected_filter_values', [])
        return render_to_response('ajaxviews/_select_multiple_filter.html', {
            'values_list': values_list,
            'selected_values': selected_values,
            'reset_button': True if selected_values else False,
            'search_input': True if len(values_list) > self.filter_search_input_by else False
        })

    def _date_filter_response(self, field):
        query_dict = self._get_queryset_all().aggregate(Min(field), Max(field))
        min_date = query_dict[field + '__min']
        max_date = query_dict[field + '__max']
        if isinstance(min_date, datetime.datetime):
            min_date = min_date.date()
        if isinstance(max_date, datetime.datetime):
            max_date = max_date.date()

        selected_dates = self.json_cfg.get('selected_filter_values', None)
        if selected_dates and not self.json_cfg.get('ignore_selected_values', False):
            selected_min_date = parse(selected_dates['min_date']).date()
            selected_max_date = parse(selected_dates['max_date']).date()
            reset_button = True
        else:
            selected_min_date = min_date
            selected_max_date = max_date
            reset_button = False
        return render_to_response('ajaxviews/_select_date_filter.html', {
            'min_date': min_date,
            'max_date': max_date,
            'selected_min_date': selected_min_date,
            'selected_max_date': selected_max_date,
            'reset_button': reset_button,
        })


class ModalPlugin(BasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modal_id = None

    @property
    def modal_base_template(self):
        return getattr(self._view, 'modal_base_template', 'ajaxviews/__modal_base.html')

    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        self.modal_id = request.GET.get('modal_id', '').replace('#', '')
        if not self.modal_id:
            self.modal_id = self.json_cfg.get('modal_id', '').replace('#', '')

    def get_context_data(self, context):
        context = super().get_context_data(context)
        if self.modal_id:
            context.update({
                'modal_id': self.modal_id,
                'generic_template': self.modal_base_template,
            })
        return context


class DetailPlugin(ModalPlugin):
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        if self.modal_id and not hasattr(self, 'form_class'):
            self.json_cfg['full_url'] = self.request.get_full_path()
        self.json_cfg['init_view_type'] = 'detailView'

    def get_queryset(self, **kwargs):
        if getattr(self._view, 'deleted_obj_lookup', False) and self._view.queryset is None and self._view.model:
            return self._view.model._default_manager.all_with_deleted()
        return self._super.get_queryset(**kwargs)

    def get_context_data(self, context):
        context = super().get_context_data(context)
        if self.request.is_ajax() and not self.request.GET.get('modal_id', False):
            context['generic_template'] = 'ajaxviews/__ajax_base.html'
        if self.request.GET.get('disable_full_view', False):
            context['disable_full_view'] = True
        if self.request.GET.get('success_url', None):
            context['success_url'] = self.request.GET['success_url']
        return context


class PluginAdapter:
    def __get__(self, instance, owner):
        def func(name, param):
            param_ = param
            for Plugin in instance._view.form_plugins:
                plugin = Plugin()
                plugin._view = instance._view
                if hasattr(plugin, name):
                    param_ = getattr(plugin, name)(param_)
            return param_
        return func


# noinspection PyUnresolvedReferences
# noinspection PyCallingNonCallable
class FormPlugin(ModalPlugin):
    csrf_protection = True
    form_set = True
    extra = PluginAdapter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.extras = []
        # if hasattr(self._view, 'form_plugins'):
        #     for plugin in self._view.form_plugins:
        #         self.extras.append(plugin(self._view.form_class))
        form_class = kwargs.get('form_class') or getattr(self._view, 'form_class', None)
        if form_class:
            if 'model' not in kwargs and hasattr(form_class.Meta, 'model'):
                self._init_kwargs['model'] = getattr(form_class.Meta, 'model')
            if hasattr(form_class.Meta, 'success_message'):
                self._init_kwargs['success_message'] = getattr(form_class.Meta, 'success_message')

    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        self.json_cfg['init_view_type'] = 'formView'

    # noinspection PyBroadException
    def get_form_kwargs(self, kwargs):
        kwargs['user'] = self.request.user
        try:
            kwargs['success_url'] = self._view.get_success_url()
        except:
            pass
        related_obj_ids = {}
        for key, value in self._view.kwargs.items():
            if '_id' in key:
                related_obj_ids[key] = value
        if related_obj_ids:
            kwargs['related_obj_ids'] = related_obj_ids
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
        self.extra('get_form_kwargs', kwargs)
        return kwargs

    def form_valid(self, form):
        success_message = self._view.success_message.format(**form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        self.extra('form_valid', form)
        if self.modal_id:
            self._view.object = form.save()
            if self.request.POST.get('modal_reload', False):
                return redirect(self.get_success_url() + '?modal_id=' + self.modal_id)
            if hasattr(form, 'json_cache'):
                return JsonResponse({'success': True, 'json_cache': form.json_cache})
            return JsonResponse({'success': True})
        else:
            return self._super.form_valid(form) or self._super.formset_valid(form)

    def get_context_data(self, context):
        context = super().get_context_data(context)
        if hasattr(self._view, 'get_form_class'):
            context['page_size'] = getattr(self._view.get_form_class().Meta, 'form_size', 'sm')
        return self.extra('get_context_data', context)

    def get_success_url(self):
        if 'success_url' in self.request.POST:
            return self.request.POST.get('success_url')
        if getattr(self._view, 'success_url', None):
            success_url = force_text(self._view.success_url)
        else:
            success_url = self._super.get_success_url()
        hashtag = self.request.GET.get('hashtag', None)
        if hashtag:
            success_url += '#' + hashtag
        return success_url

    def render_to_response(self, context, **response_kwargs):
        # ignore validation errors on GET requests
        if 'form_data' in self.request.GET:
            context['form'].errors.clear()
        return super().render_to_response(context, **response_kwargs)


# from extra_views.formsets import ModelFormSetView


# noinspection PyUnresolvedReferences
class FormSet:
    # noinspection PyUnusedLocal
    def form_valid(self, formset):
        # if create view
        if getattr(self._view.form_class.Meta, 'assign_perm', False):
            # This needs to be done also for updating formsets (remove/assign)
            for obj in self._view.object_list:
                assign_obj_perm(self.request.user, obj)


# noinspection PyUnresolvedReferences
class CreateForm:
    def form_valid(self, form):
        print('create form valid:', form)
        if getattr(form.Meta, 'assign_perm', False):
            instance = form.save()
            assign_obj_perm(self._view.request.user, instance)
            # return super().form_valid(form)

    def get_context_data(self, context):
        if hasattr(self._view.form_class.Meta, 'headline'):
            context['headline'] = 'Add ' + self._view.form_class.headline
        elif hasattr(self._view.form_class.Meta, 'headline_full'):
            context['headline'] = self._view.form_class.headline
        context['disable_full_view'] = True
        return context


# noinspection PyUnresolvedReferences
class UpdateForm:
    # noinspection PyBroadException
    def get_form_kwargs(self, kwargs):
        kwargs['save_button_name'] = 'Update'
        try:
            # url_name = self._view.request.resolver_match.url_name.replace('edit_', 'delete_')
            url_name = self._view.json_cfg['view_name'].replace('edit_', 'delete_')
            kwargs['delete_url'] = reverse(url_name, args=(self._view.object.pk,))
            if not isinstance(self.object, Group) and not self._view.request.user.has_delete_perm(self._view.model):
                kwargs.pop('delete_url', None)
        except:
            pass
        return kwargs

    def get_context_data(self, context):
        if hasattr(self._view.form_class.Meta, 'headline'):
            context['headline'] = 'Edit ' + self._view.form_class.headline
        elif hasattr(self._view.form_class.Meta, 'headline_full'):
            context['headline'] = self._view.form_class.headline_full
        context['disable_full_view'] = True
        return context


class PreviewForm:
    pass


# class DeleteMixin(FormMixin):
#     pass


# class PreviewMixin(FormMixin):
#     pass


# class ViewAdapter:
#     def __init__(self, super_obj):
#         self.super_call = super_obj
#         self.plugins = []
#
#     def __getattr__(self, name):
#         def wrapper(*args, **kwargs):
#             for plugin in self.plugins:
#                 if hasattr(plugin, name):
#                     plugin.super_call = self.super_call
#                     getattr(plugin, name)(*args, **kwargs)
#         return wrapper

# def __new__(cls, *args, **kwargs):
#     instance = super().__new__(cls)
#     for plugin in getattr(args[0], 'form_plugins'):
#
#         for name in plugin.__dict__:
#             if name.startswith('__') or name.endswith('__') or \
#                name.startswith('_') or name.endswith('_') or \
#                not isinstance(plugin.__dict__[name], types.FunctionType):
#                 continue
#
#             def decorator(func):
#                 def wrapper(param):
#                     print('wrapper >>>', param)
#                     print('name:', name)
#                     plugin._view = instance._view
#                     print(getattr(plugin, name))
#                     param = plugin.__dict__[name].__get__(plugin)(param)
#                     print('return param:', param)
#                     return func(param) if param else None
#                 return wrapper
#             print('>', name)
#             if hasattr(instance, name):
#                 setattr(instance, name, decorator(getattr(instance, name)))
#             setattr(instance, name, decorator(None))
#             # instance.__dict__[name] = decorator(None)
#     return instance
