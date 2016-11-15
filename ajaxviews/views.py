from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

try:
    from extra_views import ModelFormSetView
except ImportError:
    ModelFormSetView = type('', (), {})

from .conf import settings
from .forms import ModelFormSet
from .plugins import PluginAdapter, AjaxPlugin, ListPlugin, DetailPlugin, FormPlugin, PreviewFormPlugin,\
    FormSetPlugin, DeletePlugin, CreateForm, UpdateForm


class ViewFactory:
    """
    To reduce the use of multiple inheritance this class creates a plugin instance which controls the behavior
    of the view. Using composition instead, each method of Django's class based views is called only once and
    the plugin takes care of processing the request.

    Supported plugins:
        - list
        - detail
        - form (create, update)
        - formset (create, update)
        - formpreview (create, update)
        - delete

    :var str first arg: Name of one of the supported plugins. If not specified the base plugin will be used.
    :var str second arg: Optionally specify the type of the plugin if available.
    """
    _plugins = {
        'base': AjaxPlugin,
        'list': ListPlugin,
        'detail': DetailPlugin,
        'form': FormPlugin,
        'formset': FormSetPlugin,
        'formpreview': PreviewFormPlugin,
        'delete': DeletePlugin,
    }
    _extras = {
        'create': CreateForm,
        'update': UpdateForm,
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
    """
    This is the base view which establishes communication with the client side :class:`App`.

    It merges the optional URL parameters from the GET request with the keyword arguments retrieved from
    Django's URL conf into ``json_cfg``.

    You can control the behaviour of your views by extending from this view and by setting the :attr:`plugin`
    attribute using the :class:`ViewFactory`.

    :ivar bool ajax_view: Set to True if you have created a client side module associated with the view
        class that's inheriting from this view.
    :ivar dict json_cfg: Data parsed from incoming requests and returned in each response.
    :ivar str page_size: Define the width of the view.
    """
    ajax_view = False

    def __init__(self, *args, **kwargs):
        self.json_cfg = {}
        self.ajax_view = kwargs.pop('ajax_view', self.ajax_view)
        self._plugin = getattr(self, 'plugin', ViewFactory()).create(self, super(), **kwargs)
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
    The list view can be updated by calling :func:`View.requestView` from the client side view class.

    If you have assigned the :class:`ajaxviews.queries.AjaxQuerySet` as manager to the model class, you can
    use the ``filter_fields`` to define filter parameters for the given view. It contains a list of field paths
    that are automatically applied as filters for all requests where ``get_queryset`` is called.

    The ``selected_filter_index`` is the index to access the ``filter_fields`` list.

    Field options:
        - A string only will filter it's path by the ``selected_filter_values`` passed in the ``json_cfg``.
          This is usually a list of pk's.
        - using a tuple refines the query
            - ``('<field_path>', 'date')`` Filter date range
            - ``('<field_path>', 'set', <set_of_tuples>)`` Filter first element of tuple
            - ``('<field_path>', 'exclude')`` Ignore filter. Use ``exclude_filter`` or ``exclude_sort`` to
              only ignore one of these filters.

    The ``filter_index`` and ``sort_index`` parameters can be applied independently on different fields.

    :ivar list filter_fields: List of fields to be filtered when a ``filter_index`` is passed in the request.
        The index matches the order of the list.
    :ivar bool filter_user: Whether to filter objects the authenticated user has access to. Default is False.
    :ivar int paginate_by: Number of results by which to paginate.
    :ivar int filter_search_input_by: Number of results in list view filters by which to display a search input.
    """
    plugin = ViewFactory('list')

    def get(self, request, *args, **kwargs):
        # Called for all GET requests
        # :param request: Request object
        # :param args: Positional url arguments
        # :param kwargs: Keyword url arguments
        response = self._plugin.get(request, *args, **kwargs)
        return response or super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(**kwargs)


# noinspection PyUnresolvedReferences
class AjaxDetailView(GenericBaseView, DetailView):
    """
    The detail view can be displayed in bootstrap modals without extra implementation.
    Simply add ``.modal-link`` to an html link tag with a href that points to a view that inherits from this view.
    Or you can call :class:`View.requestModal` passing in the url of the detail view.

    If a generic form view is opened in a modal and saved, the underlying detail view is reloaded automatically
    to display the changes.
    """
    plugin = ViewFactory('detail')

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(**kwargs)


# noinspection PyUnresolvedReferences
class BaseFormView(GenericBaseView):
    """
    ..include:: < isonum.txt >
    The base view for normal and preview forms.

    The ``model`` and ``success_message`` attributes from the form meta are automatically added to the view class.

    ``related_obj_ids`` are used to pass on object pk's from the calling view to the requested view
    through url kwargs.

    If ``form_cfg`` is passed through the post request, it's passed on when initializing the form.

    ``auto_select_field`` is used to update a select field when an element has been added by using ``add_fields``
    in the forms meta class.

    Order of precedence for ``success_url``:

    ``request.POST`` > ``form_cfg`` > ``form.Meta`` (if create view) > ``view class`` > ``get_absolute_url``

    :var str template_name: The template to render the form. Default: ``ajaxviews/generic_form.html``
    """
    template_name = 'ajaxviews/generic_form.html'
    success_message = ''
    auto_delete_url = settings.AUTO_DELETE_URL

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._plugin.post(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        return self._plugin.get_form_kwargs(kwargs)

    def form_valid(self, form):
        return self._plugin.form_valid(form)

    def form_invalid(self, form):
        return self._plugin.form_invalid(form)

    def get_success_url(self):
        return self._plugin.get_success_url()

    def get_template_names(self):
        return self._plugin.get_template_names()


# noinspection PyUnresolvedReferences
class BaseFormSetView(GenericBaseView):
    # template_name = 'ajaxviews/generic_form.html'
    success_message = ''
    auto_delete_url = False
    formset_class = ModelFormSet

    # @method_decorator(csrf_exempt)
    # def dispatch(self, request, *args, **kwargs):
    #     return super().dispatch(request, *args, **kwargs)

    # def get_extra_form_kwargs(self):
    #     kwargs = super().get_extra_form_kwargs()
    #     kwargs.update(self.get_formset_kwargs())
    #     return self._plugin.get_form_kwargs(kwargs)

    def formset_valid(self, formset):
        pass

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs['success_url'] = self.get_success_url()
        return kwargs


class CreateFormView(BaseFormView, CreateView):
    plugin = ViewFactory('form', 'create')


class UpdateFormView(BaseFormView, UpdateView):
    plugin = ViewFactory('form', 'update')


class CreateFormSetView(BaseFormSetView, ModelFormSetView):
    plugin = ViewFactory('formset', 'create')


class UpdateFormSetView(BaseFormSetView, ModelFormSetView):
    plugin = ViewFactory('formset', 'update')


class PreviewCreateView(BaseFormView, CreateView):
    plugin = ViewFactory('formpreview', 'create')

    def get_form_class(self):
        return self._plugin.get_form_class()

    def process_preview(self, form):
        pass

    def done(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class PreviewUpdateView(BaseFormView, UpdateView):
    plugin = ViewFactory('formpreview', 'update')

    def get_form_class(self):
        return self._plugin.get_form_class()

    def process_preview(self, form):
        pass

    def done(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


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


# class PreviewDeleteView(BaseFormView, DeleteView):
#     plugin = ViewFactory('delete', 'preview')
