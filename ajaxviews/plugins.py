import datetime
import json

from dateutil.parser import parse
from django.core.serializers.json import DjangoJSONEncoder

from django.shortcuts import render_to_response
from django.db.models import Min, Max
from django.conf import settings
from django.utils.safestring import mark_safe

from .helpers import get_objects_for_model, construct_autocomplete_searchform


class ViewAdapter:
    def __init__(self, super_obj):
        self.super_call = super_obj
        self.plugins = []

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            for plugin in self.plugins:
                if hasattr(plugin, name):
                    plugin.super_call = self.super_call
                    getattr(plugin, name)(*args, **kwargs)
        return wrapper


class BaseMixin:
    def __init__(self, view):
        self.view = view
        self.return_param = None


class ListMixin(BaseMixin):
    ajax_view = True
    paginate_by = 10

    # def __init__(self, view):
    #     super().__init__(view)
    #     if not self.paginate_by and hasattr(settings, 'DEFAULT_PAGINATE_BY'):
    #         self.paginate_by = settings.DEFAULT_PAGINATE_BY
    #     if hasattr(settings, 'FILTER_SEARCH_INPUT_BY'):
    #         self.filter_search_input_by = settings.FILTER_SEARCH_INPUT_BY

    def dispatch(self, request, *args, **kwargs):
        self.view.json_cfg.update(kwargs.copy())
        for key, value in json.loads(request.GET.dict().get('json_cfg', '{}')).items():
            if value or value is False or value == 0:
                self.view.json_cfg[key] = value

        if request.is_ajax():
            self.view.json_cfg['ajax_load'] = True

        if 'ajax_page_nr' in self.view.json_cfg:
            self.view.kwargs['page'] = self.view.json_cfg['ajax_page_nr']

        if self.view.ajax_view:
            self.view.json_cfg['ajax_view'] = True

        self.view.json_cfg['view_name'] = request.resolver_match.url_name

    def get(self, request, *args, **kwargs):
        if 'init_view_type' not in self.view.json_cfg:
            self.view.json_cfg['init_view_type'] = 'listView'
        if self.view.json_cfg.get('filter_index', -1) >= 0:
            filter_field = self.view.filter_fields[int(self.view.json_cfg['filter_index'])]
            if isinstance(filter_field, str):
                filter_values = self.get_queryset_all().get_unique_values(filter_field)
                values_list = []
                for value in filter_values:
                    if value:
                        values_list.append((value, value))
                return self.multiple_filter_response(values_list)
            elif isinstance(filter_field, tuple):
                if len(filter_field) == 2 and filter_field[1] == 'date':
                    return self.date_filter_response(filter_field[0])
                elif len(filter_field) == 3 and (filter_field[1] == 'dict' or filter_field[1] == 'set'):
                    filter_values = self.get_queryset_all().get_unique_values(filter_field[0])
                    values_list = [(value, dict(filter_field[2])[value]) for value in filter_values if value]
                    return self.multiple_filter_response(values_list)
                else:
                    raise LookupError('Invalid filter set!')
            else:
                raise LookupError('Invalid filter field!')

    def get_queryset(self, **kwargs):
        if hasattr(self.view, 'filter_user') and self.view.filter_user:
            queryset = get_objects_for_model(self.view.request.user, self.view.model)
        else:
            queryset = self.view.get_queryset()
        if hasattr(queryset, 'default_filter'):
            opts = self.view.json_cfg.copy()
            if hasattr(self, 'filter_fields'):
                if self.view.json_cfg.get('selected_filter_index', -1) >= 0:
                    opts['filter_field'] = self.filter_fields[int(self.view.json_cfg['selected_filter_index'])]
                if self.view.json_cfg.get('sort_index', -1) >= 0:
                    opts['sort_field'] = self.filter_fields[int(self.view.json_cfg['sort_index'])]
            return queryset.default_filter(opts, **kwargs)
        return queryset

    def get_queryset_all(self):
        if hasattr(self, 'filter_user') and self.filter_user:
            return get_objects_for_model(self.view.request.user, self.view.model)
        return self.view.model.objects.all()

    def multiple_filter_response(self, values_list):
        selected_values = []
        if not self.view.json_cfg.get('ignore_selected_values', False):
            selected_values = self.view.json_cfg.get('selected_filter_values', [])
        return render_to_response('ajaxviews/_select_multiple_filter.html', {
            'values_list': values_list,
            'selected_values': selected_values,
            'reset_button': True if selected_values else False,
            'search_input': True if len(values_list) > self.view.filter_search_input_by else False
        })

    def date_filter_response(self, field):
        query_dict = self.get_queryset_all().aggregate(Min(field), Max(field))
        min_date = query_dict[field + '__min']
        max_date = query_dict[field + '__max']
        if isinstance(min_date, datetime.datetime):
            min_date = min_date.date()
        if isinstance(max_date, datetime.datetime):
            max_date = max_date.date()

        selected_dates = self.view.json_cfg.get('selected_filter_values', None)
        if selected_dates and not self.view.json_cfg.get('ignore_selected_values', False):
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

    def get_context_data(self, **kwargs):
        context = self.super_call.get_context_data(**kwargs)

        context['view_name'] = self.view.json_cfg.get('view_name', None)
        if hasattr(self, 'page_size') and self.page_size:
            context['page_size'] = self.page_size
        context['json_cfg'] = mark_safe(json.dumps(
            self.view.json_cfg, cls=DjangoJSONEncoder
        ))

        if self.view.request.is_ajax() and not self.view.request.GET.get('modal_id', False):
            context['generic_template'] = 'ajaxviews/__ajax_base.html'
        if not self.view.request.is_ajax() and hasattr(self, 'search_field'):
            context['search_form'] = construct_autocomplete_searchform(self.search_field)
        if self.view.json_cfg.get('sort_index', -1) >= 0:
            context['sort_index'] = self.view.json_cfg['sort_index']
            context['sort_order'] = self.view.json_cfg.get('sort_order', None)
        return context


class ModalMixin(BaseMixin):
    pass


class FormMixin(BaseMixin):
    csrf_protection = True


class CreateMixin(BaseMixin):
    pass


class UpdateMixin(BaseMixin):
    pass


class DeleteMixin(BaseMixin):
    pass


class PreviewMixin(BaseMixin):
    pass
