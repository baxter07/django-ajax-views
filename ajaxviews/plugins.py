import datetime
import json

from dateutil.parser import parse
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder

from django.shortcuts import render_to_response
from django.db.models import Min, Max
from django.conf import settings
from django.utils.safestring import mark_safe
from django.views.generic import CreateView
from extra_views.formsets import ModelFormSetView

from .helpers import get_objects_for_model, construct_autocomplete_searchform


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


class BaseMixin:
    def __init__(self, view):
        self._view = view

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


class ListMixin(BaseMixin):
    ajax_view = True

    def __init__(self, view):
        super().__init__(view)
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

    def get_queryset(self, super_call, **kwargs):
        if getattr(self._view, 'filter_user', False):
            queryset = get_objects_for_model(self.request.user, self.model)
        else:
            queryset = super_call.get_queryset()
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


class ModalMixin(BaseMixin):
    modal_base_template = 'ajaxviews/__modal_base.html'

    def __init__(self, view):
        super().__init__(view)
        self.modal_id = None
        if hasattr(view, 'modal_base_template'):
            self.modal_base_template = view.modal_base_template

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


class DetailMixin(ModalMixin):
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        if self.modal_id and not hasattr(self, 'form_class'):
            self.json_cfg['full_url'] = self.request.get_full_path()

    def get_queryset(self, super_call, **kwargs):
        if getattr(self._view, 'deleted_obj_lookup', False) and self._view.queryset is None and self._view.model:
            return self._view.model._default_manager.all_with_deleted()
        return super_call.get_queryset(**kwargs)


class FormMixin(ModalMixin):
    csrf_protection = True
    form_set = True

    def __init__(self, view):
        super().__init__(view)
        for base in view.__class__.__bases__:
            if isinstance(base, ModelFormSetView):
                self.form_set = True


class CreateMixin(FormMixin):
    pass


class UpdateMixin(FormMixin):
    pass


class DeleteMixin(FormMixin):
    pass


class PreviewMixin(FormMixin):
    pass
