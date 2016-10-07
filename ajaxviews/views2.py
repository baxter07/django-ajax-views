import types

from django.forms.models import BaseModelFormSet
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .plugins import BaseMixin, ListMixin, DetailMixin, FormMixin, PreviewMixin, DeleteMixin


class ModelFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(self.forms) > 0:
            self.form_action = self.forms[0].helper.form_action
            self.render_form_actions = self.forms[0].render_form_actions()
            self.helper.layout = self.forms[0].helper.layout

    def get_headline(self):
        return ''

try:
    from extra_views import ModelFormSetView
except ImportError:
    ModelFormSetView = type('', (), {})
else:
    def get_form_kwargs(self):
        return {}
    ModelFormSetView.get_form_kwargs = types.MethodType(get_form_kwargs, ModelFormSetView)
    ModelFormSetView.formset_class = ModelFormSet


# from .plugins import ViewAdapter


class GenericBaseView:
    ajax_view = False

    # def __new__(cls, *args, **kwargs):
    #     instance = super().__new__(cls, *args, **kwargs)
    #     for plugin in cls.plugins:
    #         for name in plugin.__dict__:
    #             if name.startswith('__') and name.endswith('__')\
    #                     or not isinstance(plugin.__dict__[name], types.FunctionType):
    #                 continue
    #             instance.__dict__[name] = plugin.__dict__[name].__get__(instance)
    #     return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.adapter = ViewAdapter(super())
        # if hasattr(self, 'plugins'):
        #     for plugin_class in self.plugins:
        #         self.adapter.plugins.append(plugin_class(self))
        self.json_cfg = {}
        if not self.ajax_view:
            self.ajax_view = kwargs.pop('ajax_view', False)
        self._plugin = self.plugin(self) if hasattr(self, 'plugin') else BaseMixin(self)

    def dispatch(self, request, *args, **kwargs):
        self._plugin.dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self._plugin.get_context_data(context)


class AjaxListView(GenericBaseView, ListView):
    plugin = ListMixin

    def get(self, request, *args, **kwargs):
        response = self._plugin.get(request, *args, **kwargs)
        return response if response else super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(super(), **kwargs)
        # return super().get_queryset(**kwargs)


class GenericDetailView(GenericBaseView, DetailView):
    plugin = DetailMixin

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(super(), **kwargs)


class BaseFormView(GenericBaseView):
    plugin = FormMixin

    def get_success_url(self):
        return super().get_success_url()

    def get_form_kwargs(self, **kwargs):
        return super().get_form_kwargs(**kwargs)


class GenericCreateView(BaseFormView, CreateView):
    plugin = FormMixin

    def form_valid(self, form):
        return super().form_valid(form)


class FormSetCreateView(BaseFormView, ModelFormSetView):
    def formset_valid(self, formset):
        return super().formset_valid(formset)


class PreviewCreateView(BaseFormView, CreateView):
    pass


class GenericUpdateView(BaseFormView, UpdateView):
    pass


class FormSetUpdateView(BaseFormView, ModelFormSetView):
    pass


class PreviewUpdateView(BaseFormView, UpdateView):
    pass


class GenericDeleteView(BaseFormView, DeleteView):
    pass


class PreviewDeleteView(BaseFormView, DeleteView):
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
