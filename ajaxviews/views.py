import types

from django.forms.models import BaseModelFormSet
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import DefaultFormHelper
from .plugins import PluginAdapter, AjaxPlugin, ListPlugin, DetailPlugin, FormPlugin, DeletePlugin, FormSetPlugin, \
    CreateForm, UpdateForm, PreviewForm


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
    # ModelFormSetView.get_form_kwargs = types.MethodType(lambda self: {}, ModelFormSetView)
    ModelFormSetView.get_form_kwargs = types.MethodType(get_form_kwargs, ModelFormSetView)
    ModelFormSetView.formset_class = ModelFormSet


class ViewFactory:
    _plugins = {
        'base': AjaxPlugin,
        'list': ListPlugin,
        'detail': DetailPlugin,
        'form': FormPlugin,
        'formset': FormSetPlugin,
        'delete': DeletePlugin,
    }
    _extras = {
        'create': CreateForm,
        'update': UpdateForm,
        'preview': PreviewForm,
    }

    def __init__(self, *args):
        self.name = 'base'
        self.extra_names = []
        if len(args) == 1:
            if args[0] not in self._plugins:
                raise LookupError('Plugin {} not supported!'.format(args[0]))
            self.name = args[0]
        elif len(args) > 1:
            for extra in args[1:]:
                if extra not in self._extras:
                    raise LookupError('Extension plugin {} not supported!'.format(extra))
            self.name = args[0]
            self.extra_names = args[1:]

    def create(self, view, super_call, **kwargs):
        instance = self._plugins[self.name](view, **kwargs)
        instance.super = super_call
        control_list = []
        for name in self.extra_names:
            extra = self._extras[name]()
            extra.plugin = instance
            extra.view = view
            extra.super = super_call
            control_list.append(extra)
        instance.extra = PluginAdapter(control_list)
        return instance


class GenericBaseView:
    ajax_view = False

    def __init__(self, *args, **kwargs):
        self.json_cfg = {}
        self.ajax_view = kwargs.pop('ajax_view', self.ajax_view)
        if hasattr(self, 'plugin'):
            self._plugin = self.plugin.create(self, super(), **kwargs)
        else:
            self._plugin = ViewFactory().create(self, super(), **kwargs)
        if self._plugin.view_kwargs:
            kwargs.update(self._plugin.view_kwargs)
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self._plugin.dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self._plugin.get_context_data(context)


# noinspection PyUnresolvedReferences
class AjaxListView(GenericBaseView, ListView):
    """
    The ListView can be updated by calling :func:`View.requestView` from client side view class.

    :ivar int paginate_by: number of results in list by which to paginate.
    :ivar int filter_search_input_by: number of results in list view filters by which to display a search input.
    """
    plugin = ViewFactory('list')
    # plugin = ListPlugin

    def get(self, request, *args, **kwargs):
        response = self._plugin.get(request, *args, **kwargs)
        return response or super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(**kwargs)


# noinspection PyUnresolvedReferences
class AjaxDetailView(GenericBaseView, DetailView):
    plugin = ViewFactory('detail')

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(**kwargs)


# noinspection PyUnresolvedReferences
class BaseFormView(GenericBaseView):
    template_name = 'ajaxviews/generic_form.html'
    success_message = ''

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


# noinspection PyUnresolvedReferences
class BaseFormSetView(GenericBaseView):
    template_name = 'ajaxviews/generic_form.html'
    success_message = ''

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # def get(self, request, *args, **kwargs):
    #     formset = self.construct_formset()
    #     return self.render_to_response(
    #         self.get_context_data(formset=formset),
    #         context=RequestContext(request),
    #     )

    def get_extra_form_kwargs(self):
        kwargs = super().get_extra_form_kwargs()
        kwargs.update(self.get_form_kwargs())
        return self._plugin.get_form_kwargs(kwargs)

    def get_formset(self):
        formset = super().get_formset()
        formset.helper = DefaultFormHelper()
        formset.helper.form_tag = False
        return formset

    def formset_valid(self, formset):
        self._plugin.form_valid(formset)
        return super().formset_valid(formset)

    # def formset_invalid(self, formset):
    #     return self.render_to_response(
    #         self.get_context_data(formset=formset),
    #         context=RequestContext(request),
    #     )

    def get_success_url(self):
        return self._plugin.get_success_url()

    # def render_to_response(self, context, **kwargs):
    #     pass


class CreateFormView(BaseFormView, CreateView):
    plugin = ViewFactory('form', 'create')

    # def __init__(self, **kwargs):
    #     form_class = kwargs.get('form_class') or getattr(self, 'form_class', None)
    #     if form_class and hasattr(form_class.Meta, 'success_url'):
    #         kwargs['success_url'] = getattr(form_class.Meta, 'success_url')
    #     super().__init__(**kwargs)


# noinspection PyUnresolvedReferences
class CreateFormSetView(BaseFormSetView, ModelFormSetView):
    plugin = ViewFactory('formset', 'create')


class PreviewCreateView(BaseFormView, CreateView):
    plugin = ViewFactory('form', 'create', 'preview')


class UpdateFormView(BaseFormView, UpdateView):
    plugin = ViewFactory('form', 'update')


class UpdateFormSetView(BaseFormSetView, ModelFormSetView):
    plugin = ViewFactory('formset', 'update')


class PreviewUpdateView(BaseFormView, UpdateView):
    plugin = ViewFactory('form', 'update', 'preview')


# noinspection PyUnresolvedReferences
class DeleteFormView(GenericBaseView, DeleteView):
    plugin = ViewFactory('delete')

    def get(self, request, *args, **kwargs):
        return self._plugin.get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._plugin.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self._plugin.delete(request, *args, **kwargs)

    def get_success_url(self):
        return self._plugin.get_success_url()


class PreviewDeleteView(BaseFormView, DeleteView):
    plugin = ViewFactory('delete', 'preview')
