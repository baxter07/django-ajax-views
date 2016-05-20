import types
import datetime
from dateutil.parser import parse

from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.forms.models import BaseModelFormSet
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.conf import settings
from django.db.models import Min, Max
from django.shortcuts import render_to_response

from extra_views import ModelFormSetView

from .mixins import CsrfExemptMixin, AjaxMixin, EditMixin, ModalMixin, ModalFormMixin, PreviewMixin
from .helpers import get_objects_for_model, assign_obj_perm, remove_obj_perm, construct_autocomplete_searchform


class ModelFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(self.forms) > 0:
            self.form_action = self.forms[0].helper.form_action
            self.render_form_actions = self.forms[0].render_form_actions()
            self.helper.layout = self.forms[0].helper.layout
        # if hasattr(self.forms[0], 'headline'):
        #     self.headline = self.forms[0].headline
        # elif hasattr(self.forms[0], 'headline_full'):
        #     self.headline_full = self.forms[0].headline
        # self.queryset = Model.objects.all()

    def get_headline(self):
        return ''


def get_form_kwargs(self):
    return {}

ModelFormSetView.get_form_kwargs = types.MethodType(get_form_kwargs, ModelFormSetView)
ModelFormSetView.formset_class = ModelFormSet


class AjaxListView(LoginRequiredMixin, AjaxMixin, ListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.paginate_by and hasattr(settings, 'DEFAULT_PAGINATE_BY'):
            self.paginate_by = settings.DEFAULT_PAGINATE_BY
        if hasattr(settings, 'FILTER_SEARCH_INPUT_BY'):
            self.filter_search_input_by = settings.FILTER_SEARCH_INPUT_BY

    def get(self, request, *args, **kwargs):
        if self.json_cfg.get('filter_index', -1) >= 0:
            filter_field = self.filter_fields[int(self.json_cfg['filter_index'])]
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
                    raise Exception('Invalid filter set!')
            else:
                raise Exception('Invalid filter field!')
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        if hasattr(self, 'filter_user') and self.filter_user:
            queryset = get_objects_for_model(self.request.user, self.model)
        else:
            queryset = super().get_queryset()
        if hasattr(queryset, 'default_filter'):
            opts = self.json_cfg.copy()
            if hasattr(self, 'filter_fields'):
                if self.json_cfg.get('selected_filter_index', -1) >= 0:
                    opts['filter_field'] = self.filter_fields[int(self.json_cfg['selected_filter_index'])]
                if self.json_cfg.get('sort_index', -1) >= 0:
                    opts['sort_field'] = self.filter_fields[int(self.json_cfg['sort_index'])]
            return queryset.default_filter(opts, **kwargs)
        return queryset

    def get_queryset_all(self):
        if hasattr(self, 'filter_user') and self.filter_user:
            return get_objects_for_model(self.request.user, self.model)
        return self.model.objects.all()

    def multiple_filter_response(self, values_list):
        selected_values = []
        if not self.json_cfg.get('ignore_selected_values', False):
            selected_values = self.json_cfg.get('selected_filter_values', [])
        return render_to_response('ajaxviews/_select_multiple_filter.html', {
            'values_list': values_list,
            'selected_values': selected_values,
            'reset_button': True if selected_values else False,
            'search_input': True if len(values_list) > self.filter_search_input_by else False
        })

    def date_filter_response(self, field):
        query_dict = self.get_queryset_all().aggregate(Min(field), Max(field))
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.is_ajax() and not self.request.GET.get('modal_id', False):
            context['generic_template'] = 'ajaxviews/__ajax_base.html'
        if not self.request.is_ajax() and hasattr(self, 'search_field'):
            context['search_form'] = construct_autocomplete_searchform(self.search_field)
        if self.json_cfg.get('sort_index', -1) >= 0:
            context['sort_index'] = self.json_cfg['sort_index']
            context['sort_order'] = self.json_cfg.get('sort_order', None)
        if 'init_view_type' not in self.json_cfg:
            self.json_cfg['init_view_type'] = 'listView'
        return context


class GenericDetailView(LoginRequiredMixin, ModalMixin, AjaxMixin, DetailView):
    deleted_obj_lookup = True

    def get_queryset(self):
        if self.queryset is None:
            if self.model:
                if self.deleted_obj_lookup:
                    return self.model._default_manager.all_with_deleted()
                return self.model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a QuerySet. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_queryset()." % {
                        'cls': self.__class__.__name__
                    }
                )
        return self.queryset.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.is_ajax() and not self.request.GET.get('modal_id', False):
            context['generic_template'] = 'ajaxviews/__ajax_base.html'
        if 'init_view_type' not in self.json_cfg:
            self.json_cfg['init_view_type'] = 'detailView'
        if self.request.GET.get('disable_full_view', False):
            context['disable_full_view'] = True
        if self.request.GET.get('success_url', None):
            context['success_url'] = self.request.GET['success_url']
        return context


class CreateViewMixin(EditMixin, AjaxMixin):
    template_name = 'ajaxviews/generic_form.html'

    def __init__(self, **kwargs):
        if 'form_class' in kwargs and hasattr(kwargs['form_class'].Meta, 'success_url'):
            kwargs['success_url'] = getattr(kwargs['form_class'].Meta, 'success_url')
        elif hasattr(self, 'form_class') and self.form_class and hasattr(self.form_class.Meta, 'success_url'):
            kwargs['success_url'] = getattr(self.form_class.Meta, 'success_url')
        super().__init__(**kwargs)

    def form_valid(self, form):
        if hasattr(form.Meta, 'assign_perm') and getattr(form.Meta, 'assign_perm'):
            instance = form.save()
            assign_obj_perm(self.request.user, instance)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.form_class.Meta, 'headline'):
            context['headline'] = 'Add ' + self.form_class.headline
        elif hasattr(self.form_class.Meta, 'headline_full'):
            context['headline'] = self.form_class.headline
        context['disable_full_view'] = True
        return context


class GenericCreateView(CsrfExemptMixin, LoginRequiredMixin, ModalFormMixin, CreateViewMixin, CreateView):
    pass


class FormSetCreateView(CsrfExemptMixin, LoginRequiredMixin, CreateViewMixin, ModelFormSetView):
    def formset_valid(self, formset):
        response = super().formset_valid(formset)
        if hasattr(self.form_class.Meta, 'assign_perm') and getattr(self.form_class.Meta, 'assign_perm'):
            # This needs to be done also for updating formsets (remove/assign)
            for obj in self.object_list:
                assign_obj_perm(self.request.user, obj)
        return response


class PreviewCreateView(CsrfExemptMixin, LoginRequiredMixin, ModalFormMixin, PreviewMixin, CreateViewMixin, CreateView):
    preview_template_name = 'ajaxviews/generic_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self._stage == 1:
            kwargs['save_button_name'] = 'Create'
        else:
            kwargs['save_button_name'] = 'Update'
        return kwargs


class UpdateViewMixin(EditMixin, AjaxMixin):
    template_name = 'ajaxviews/generic_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['save_button_name'] = 'Update'
        try:
            url_name = self.request.resolver_match.url_name.replace('edit_', 'delete_')
            kwargs['delete_url'] = reverse(url_name, args=(self.object.pk,))
            if not isinstance(self.object, Group) and not self.request.user.has_delete_perm(self.model):
                kwargs.pop('delete_url', None)
        except:
            pass
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.form_class.Meta, 'headline'):
            context['headline'] = 'Edit ' + self.form_class.headline
        elif hasattr(self.form_class.Meta, 'headline_full'):
            context['headline'] = self.form_class.headline
        context['disable_full_view'] = True
        return context


class GenericUpdateView(CsrfExemptMixin, LoginRequiredMixin, ModalFormMixin, UpdateViewMixin, UpdateView):
    pass


class FormSetUpdateView(CsrfExemptMixin, LoginRequiredMixin, UpdateViewMixin, ModelFormSetView):
    pass


class PreviewUpdateView(CsrfExemptMixin, LoginRequiredMixin, ModalFormMixin, PreviewMixin, UpdateViewMixin, UpdateView):
    preview_template_name = 'ajaxviews/generic_form.html'


class GenericDeleteView(LoginRequiredMixin, DeleteView):
    def get(self, request, *args, **kwargs):
        if request.GET.get('delete_file', False):
            instance = self.get_object()
            if instance.file:
                instance.file.delete(False)
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'remove_obj_perm' in kwargs:
            remove_obj_perm(self.request.user, self.get_object())
        return super().post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Entry successfully deleted!')
        return response

    def get_success_url(self):
        try:
            instance = self.get_object()
            instance.pk = None
            return instance.get_absolute_url()
        except:
            if 'success_url' in self.request.GET:
                return self.request.GET.get('success_url')
            return super().get_success_url()


class PreviewDeleteView(LoginRequiredMixin, PreviewMixin, DeleteView):
    pass


# selected_ids = []
# if not self.json_cfg.get('ignore_selected_ids', False):
#     selected_ids = self.json_cfg.get('selected_filter_ids', [])
# attr_list = []
# for attr in filter_values:
#     if attr:
#         pk_key = list(attr.keys())[0]
#         if 'pk' in str(pk_key):
#             value_key = list(attr.keys())[1]
#         else:
#             pk_key = list(attr.keys())[1]
#             value_key = list(attr.keys())[0]
#         if not attr[value_key]:
#             continue
#         attr_dict = {
#             'name': pk_key,
#             'value': attr[pk_key],
#             'text': attr[value_key],
#             'checked': False
#         }
#         if not selected_ids:
#             attr_dict['checked'] = True
#         elif attr[pk_key] in selected_ids:
#             attr_dict['checked'] = True
#         attr_list.append(attr_dict)
