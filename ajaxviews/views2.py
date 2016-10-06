import types

from django.forms.models import BaseModelFormSet
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .plugins import ListMixin, FormMixin, ModalMixin, PreviewMixin, DeleteMixin
from .mixins import FormMixin, ModalMixin, PreviewMixin, AjaxMixin


class ModelFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(self.forms) > 0:
            self.form_action = self.forms[0].helper.form_action
            self.render_form_actions = self.forms[0].render_form_actions()
            self.helper.layout = self.forms[0].helper.layout

    def get_headline(self):
        return ''


def get_form_kwargs(self):
    return {}

try:
    from extra_views import ModelFormSetView
except ImportError:
    ModelFormSetView = type('', (), {})
else:
    ModelFormSetView.get_form_kwargs = types.MethodType(get_form_kwargs, ModelFormSetView)
    ModelFormSetView.formset_class = ModelFormSet


from .plugins import ViewAdapter


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
        self.json_cfg = {}
        self.adapter = ViewAdapter(super())
        if hasattr(self, 'plugins'):
            for plugin_class in self.plugins:
                self.adapter.plugins.append(plugin_class(self))

    def dispatch(self, request, *args, **kwargs):
        self.adapter.dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print('>> get_context_data', context)
        return self.adapter.get_context_data(**context)


class AjaxListView(GenericBaseView, ListView):
    plugins = [ListMixin]

    def get_queryset(self, **kwargs):
        return super().get_queryset(**kwargs)


class GenericDetailView(GenericBaseView, DetailView):
    plugins = [ModalMixin]

    def get_queryset(self, **kwargs):
        return super().get_queryset(**kwargs)


class BaseFormView(GenericBaseView):
    def get_success_url(self):
        return super().get_success_url()

    def get_form_kwargs(self, **kwargs):
        return super().get_form_kwargs(**kwargs)


class GenericCreateView(BaseFormView, CreateView):
    plugins = [FormMixin, ModalMixin]

    def form_valid(self, form):
        return super().form_valid(form)


class FormSetCreateView(BaseFormView, ModelFormSetView):
    plugins = [FormMixin, ModalMixin]

    def formset_valid(self, formset):
        return super().formset_valid(formset)


class PreviewCreateView(BaseFormView, CreateView):
    plugins = [FormMixin, PreviewMixin, ModalMixin]


class GenericUpdateView(BaseFormView, UpdateView):
    plugins = [FormMixin, ModalMixin]


class FormSetUpdateView(BaseFormView, ModelFormSetView):
    plugins = [FormMixin, ModalMixin]


class PreviewUpdateView(BaseFormView, UpdateView):
    plugins = [FormMixin, PreviewMixin, ModalMixin]


class GenericDeleteView(BaseFormView, DeleteView):
    plugins = [DeleteMixin, ModalMixin]


class PreviewDeleteView(BaseFormView, DeleteView):
    plugins = [DeleteMixin, PreviewMixin, ModalMixin]


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
