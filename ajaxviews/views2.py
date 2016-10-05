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
        # if hasattr(self.forms[0], 'headline'):
        #     self.headline = self.forms[0].headline
        # elif hasattr(self.forms[0], 'headline_full'):
        #     self.headline_full = self.forms[0].headline
        # self.queryset = Model.objects.all()

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


class BaseViewMixin:
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

    def __init__(self, **kwargs):
        self.adapter = ViewAdapter(self, self.plugins)
        self.plugin = self.plugins[0](self)
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        # _args, _kwargs = self.adapter.run('dispatch', *args, **kwargs)
        # print('>>', _args, _kwargs)
        self.plugin.dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.plugin.get_context_data(**context)


class AjaxListView(BaseViewMixin, ListView):
    plugins = [ListMixin]


class GenericDetailView(BaseViewMixin, DetailView):
    plugins = [ModalMixin]


class GenericCreateView(BaseViewMixin, CreateView):
    plugins = [FormMixin, ModalMixin]


class FormSetCreateView(BaseViewMixin, ModelFormSetView):
    plugins = [FormMixin, ModalMixin]


class PreviewCreateView(BaseViewMixin, CreateView):
    plugins = [FormMixin, PreviewMixin, ModalMixin]


class GenericUpdateView(BaseViewMixin, UpdateView):
    plugins = [FormMixin, ModalMixin]


class FormSetUpdateView(BaseViewMixin, ModelFormSetView):
    plugins = [FormMixin, ModalMixin]


class PreviewUpdateView(BaseViewMixin, UpdateView):
    plugins = [FormMixin, PreviewMixin, ModalMixin]


class GenericDeleteView(BaseViewMixin, DeleteView):
    plugins = [DeleteMixin, ModalMixin]


class PreviewDeleteView(BaseViewMixin, DeleteView):
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
