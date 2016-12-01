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
    To reduce the use of multiple inheritance in django views, this class creates a plugin instance which controls
    the behavior of the view. Using composition instead, each method of Django's class based views is called only
    once and the plugin takes care of processing the request.

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

    It merges the query string from the GET request with the keyword arguments retrieved from
    Django's URL conf into ``json_cfg``.

    You can control the behaviour of your views by extending from this view and setting the :attr:`plugin`
    class attribute.

    :ivar object plugin: Process the request using the :class:`ViewFactory`.
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
    set a ``filter_fields`` attribute to the view class to specify filter parameters. It contains a list of
    field paths that are automatically applied as filters for all requests where ``get_queryset`` is called.

    The index of the ``filter_fields`` list is passed between requests to control the filter and sorting mechanism.
    Add a table in your templates with the following markup to activate generic filters from :class:`FilterView`.

    .. code-block:: html

        <tr class="filter-header">
          <th data-filter-index="0">
            <span>Column Header Name</span> {% include 'ajaxviews/_table_sort.html' with index=0 %}
          </th>
          <th data-filter-index="1">
            <span>Column Header Name</span> {% include 'ajaxviews/_table_sort.html' with index=1 %}
          </th>
        </tr>

    The ``.filter-header`` is only necessary if you want to use the built-in
    `view styles <../setup.html#stylus-css>`_ to style the popover which displays the filter values of the current
    filter index.

    .. The ``selected_filter_index`` is the index to access the ``filter_fields`` list.

    Field options for ``filter_fields``:

        - A **string** only ``'<field_path>'`` will filter it's path by the ``selected_filter_values`` passed in
          the ``json_cfg``. This is usually a list of pk's or the fields values.
        - using a **tuple** refines the query

            - ``('<field_path>', 'date')`` Filter by date range
            - ``('<field_path>', 'set', <set_of_tuples>)`` Filter by first element of tuple
            - ``('<field_path>', 'exclude')`` Ignore filter, use ``exclude_filter`` or ``exclude_sort`` to
              only ignore one of these.

    The ``filter_index`` and ``sort_index`` parameters can be applied independently on different fields.

    :ivar list filter_fields: List of fields to be filtered when a ``selected_filter_index`` and
        ``selected_filter_values`` are passed in the request. The index matches the order of the list.
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
    The detail view can be displayed in bootstrap modals. Simply add ``.modal-link`` to an html link tag with
    a href that points to a view that inherits from this view. Or you can call :class:`View.requestModal` passing
    in the url of the detail view.

    If a :class:`ajaxviews.forms.GenericModelForm` is opened in a modal and saved, the underlying detail view is
    reloaded automatically to display the changes.
    """
    plugin = ViewFactory('detail')

    def get_queryset(self, **kwargs):
        return self._plugin.get_queryset(**kwargs)


# noinspection PyUnresolvedReferences
class BaseFormView(GenericBaseView):
    """
    .. include:: <isonum.txt>

    This is the base view for normal and preview forms.

    The ``model`` and ``success_message`` attributes from the form meta are automatically added to the view class.

    ``related_obj_ids`` are used to pass on object pk's from the calling view to the requested view
    through url kwargs. This is useful if a model has relations (e.g. fk, m2m) it is depending on to be saved.

    If ``form_cfg`` is passed in the post request (by default as hidden input field), it's accessible through
    the forms ``cleaned_form_cfg`` property.

    The ``auto_select_field`` coming from a GET request is used to update a select field when an element has been
    added by using ``add_fields`` in the forms meta class.

    There are multiple ways to set a success url for the form view.
    This is the order of precedence for ``success_url``:

    ``request.POST`` |rarr| ``form_cfg`` |rarr| ``form.Meta`` (if create view) |rarr| ``view class`` |rarr|
    ``get_absolute_url``

    :var str template_name: The template to render the form. Default: ``'ajaxviews/generic_form.html'``
    :var str success_message: Message to display on successful form save. Default: ``''``
    :var str form_actions_template: Action buttons rendered at the bottom of the form.
        Default: ``'ajaxviews/_form_controls.html'``
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
    """
    This view renders a formset using the ``ModelFormSetView`` class from ``django-extra-views``.

    The ``success_url`` is passed on to the formset and a message is displayed on successful form save if
    ``success_message`` has been added to the view class.
    """
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
        self._plugin.formset_valid(formset)
        return super().formset_valid(formset)

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs['success_url'] = self.get_success_url()
        return kwargs


class CreateFormView(BaseFormView, CreateView):
    """
    .. Use the form meta's ``success_url`` to redirect the view to.

    Form view used to create model objects. Inherits functionality from :class:`BaseFormView`.

    Assign django-guardian's object permissions if ``assign_perm`` attribute has been added to the class.

    :var str headline_prefix: The prefix to prepend to the headline which is specified in the form meta.
        Default: ``Add``
    :var bool assign_perm: Save object permissions for new model instance of authenticated user.
        Default: ``False``
    """
    plugin = ViewFactory('form', 'create')


class UpdateFormView(BaseFormView, UpdateView):
    """
    Form view used to update model objects. Inherits functionality from :class:`BaseFormView`.

    :var str headline_prefix: The prefix to prepend to the headline which is specified in the form meta.
        Default: ``Update``
    :var bool auto_delete_url: Wheter or not to use ``AUTO_DELETE_URL``. Default: ``True``
    :var str delete_url: Parse delete url for the current view using a naming convention.
        View name: ``edit_<name>`` |rarr| ``delete_<name>`` Default: ``True``
    """
    plugin = ViewFactory('form', 'update')


class CreateFormSetView(BaseFormSetView, ModelFormSetView):
    """
    FormSet view used to create multiple model objects. Inherits functionality from :class:`BaseFormSetView`.

    :var str headline_prefix: The prefix to prepend to the headline. Default: ``Add``
    """
    plugin = ViewFactory('formset', 'create')


class UpdateFormSetView(BaseFormSetView, ModelFormSetView):
    """
    FormSet view used to update multiple model objects. Inherits functionality from :class:`BaseFormSetView`.

    :var str headline_prefix: The prefix to prepend to the headline. Default: ``Update``
    """
    plugin = ViewFactory('formset', 'update')


class PreviewCreateView(BaseFormView, CreateView):
    """
    Preview for model forms to confirm actions.

    Stages:
        - 0 - GET: display model form
        - 1 - POST: submitted model form and render preview form (process_preview)
        - 2 - POST: submitted preview form and save model form (done)

    :param str preview_template_name: Template to use to render the preview.
        Default: ``'ajaxviews/generic_form.html'``
    :param object preview_form_class: Form class to use for preview stage e.g. :class:`SimpleForm`.
    """
    plugin = ViewFactory('formpreview', 'create')

    def get_form_class(self):
        return self._plugin.get_form_class()

    def process_preview(self, form):
        pass

    def done(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class PreviewUpdateView(BaseFormView, UpdateView):
    """
    Works the same as :class:`PreviewCreateView` except for updating model objects.
    """
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
