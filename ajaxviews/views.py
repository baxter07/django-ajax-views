import types

from django.forms.models import BaseModelFormSet
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .plugins import BasePlugin, ListPlugin, DetailPlugin, FormPlugin, CreateForm, UpdateForm, PreviewForm, FormSet
from .forms import DefaultFormHelper


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


class GenericBaseView:
    ajax_view = False

    def __init__(self, *args, **kwargs):
        self.json_cfg = {}
        self.ajax_view = kwargs.pop('ajax_view', False) or getattr(self, 'ajax_view', False)
        if hasattr(self, 'plugin'):
            self._plugin = self.plugin(self, super(), **kwargs)
        else:
            self._plugin = BasePlugin(self, super(), **kwargs)
        if self._plugin._init_kwargs:
            kwargs.update(self._plugin._init_kwargs)
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self._plugin.dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self._plugin.get_context_data(context)


class AjaxListView(GenericBaseView, ListView):
    """
    The ListView can be updated by calling :func:`View.requestView` from client side view class.

    :ivar int paginate_by: number of results in list by which to paginate.
    :ivar int filter_search_input_by: number of results in list view filters by which to display a search input.
    """
    plugin = ListPlugin

    def get(self, request, *args, **kwargs):
        response = self._plugin.get(request, *args, **kwargs)
        return response or super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(**kwargs)


class GenericDetailView(GenericBaseView, DetailView):
    plugin = DetailPlugin

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(**kwargs)


class BaseFormView(GenericBaseView):
    template_name = 'ajaxviews/generic_form.html'
    success_message = ''
    plugin = FormPlugin

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        return self._plugin.get_form_kwargs(kwargs)

    def form_valid(self, form):
        return self._plugin.form_valid(form)

    def get_success_url(self):
        return self._plugin.get_success_url()


class FormSetMixin:
    def get_extra_form_kwargs(self):
        kwargs = super().get_extra_form_kwargs()
        kwargs.update(self.get_form_kwargs())
        return kwargs

    def get_formset(self):
        formset = super().get_formset()
        formset.helper = DefaultFormHelper()
        formset.helper.form_tag = False
        return formset


class CreateFormView(BaseFormView, CreateView):
    form_plugins = [CreateForm]

    def __init__(self, **kwargs):
        form_class = kwargs.get('form_class') or getattr(self, 'form_class', None)
        if form_class and hasattr(form_class.Meta, 'success_url'):
            kwargs['success_url'] = getattr(form_class.Meta, 'success_url', None)
        super().__init__(**kwargs)


class CreateFormSetView(BaseFormView, FormSetMixin, ModelFormSetView):
    form_plugins = [CreateForm, FormSet]

    def formset_valid(self, formset):
        self._plugin.form_valid(formset)
        return super().formset_valid(formset)


class PreviewCreateView(BaseFormView, CreateView):
    plugin_extras = [CreateForm, PreviewForm]


class UpdateFormView(BaseFormView, UpdateView):
    form_plugins = [UpdateForm]


class UpdateFormSetView(BaseFormView, FormSetMixin, ModelFormSetView):
    form_plugins = [UpdateForm, FormSet]


class PreviewUpdateView(BaseFormView, UpdateView):
    form_plugins = [UpdateForm, PreviewForm]


class DeleteFormView(BaseFormView, DeleteView):
    pass


class PreviewDeleteView(BaseFormView, DeleteView):
    pass


# deprecated #########

class CreateViewMixin:
    pass


class UpdateViewMixin:
    pass


class GenericCreateView(CreateFormView):
    pass


class GenericUpdateView(UpdateFormView):
    pass


class GenericDeleteView(DeleteFormView):
    pass
