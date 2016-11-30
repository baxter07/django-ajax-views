try:
    import autocomplete_light.shortcuts as al
except ImportError:
    pass

try:
    from guardian.shortcuts import assign_perm, remove_perm, get_perms_for_model, get_objects_for_user
except ImportError:
    pass

from django.forms import Form, Select, SelectMultiple, DateInput
from django.forms.widgets import DateTimeBaseInput

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FieldWithButtons, StrictButton


def get_objects_for_model(user, model, perm_prefix='access_'):
    """
    Shortcut to return objects of a model for an authenticated user with permissions.
    This uses guardians ``get_objects_for_user`` function.

    >>> get_objects_for_model(request.user, ModelClass)
    <queryset>

    :param user: Authenticated user
    :param model: Django model instance
    :param perm_prefix: Default: ``access_``
    :return: None if no permission else QuerySet
    """
    package, __ = model.__module__.split('.')

    for perm in get_perms_for_model(model):
        if perm_prefix in perm.codename:
            return get_objects_for_user(user, package + '.' + perm.codename)
    return None


def get_model_perm(user, model, perm_prefix='access_'):
    group_permissions = user.groups.first().permissions.all()
    package, __ = model.__module__.split('.')

    for perm in get_perms_for_model(model):
        if perm_prefix in perm.codename and perm in group_permissions:
            return package + '.' + perm.codename
    return None


def assign_obj_perm(user, obj):
    permission = get_model_perm(user, obj.__class__)
    if not permission:
        raise PermissionError('No permissions to save object.')
    if not user.has_perm(permission, obj):
        assign_perm(permission, user, obj)
        return True
    return False


def remove_obj_perm(user, obj):
    permission = get_model_perm(user, obj.__class__)
    if not permission:
        raise PermissionError('No permissions to remove object.')
    if user.has_perm(permission, obj):
        remove_perm(permission, user, obj)
        return True
    return False


class DateWidget(DateInput):
    """
    Django DateInput widget which renders a bootstrap input group addon with a calendar glyphicon around
    the input field.
    """
    def render(self, *args, **kwargs):
        html_input = super().render(*args, **kwargs)
        return """<div class="input-group date">{0}
                    <div class="input-group-addon">
                      <span class="glyphicon glyphicon-calendar"></span>
                    </div>
                  </div>
               """.format(html_input)


def init_dateinput(field_items):
    """
    Assing the :class:`DateWidget` to all django fields which derive from :class:`DateTimeBaseInput` and
    add ``.dateinput`` to the widget's html class attribute.

    :param dict field_items: Django field items
    """
    for name, field in field_items:
        if isinstance(field.widget, DateTimeBaseInput):
            field.widget = DateWidget()
            field.widget.attrs['class'] = 'dateinput'
            # field.widget.attrs['data-date-format'] = 'yyyy-mm-dd'


def init_chosen_widget(field_items, disable_help_text=True):
    """
    Add ``.chosen-widget`` html class attribute to all fields of type ``Select`` or ``SelectMultiple``.

    :param field_items: Django field items
    :param bool disable_help_text: Disable the fields help text. Default: True
    """
    for name, field in field_items:
        if isinstance(field.widget, SelectMultiple) or isinstance(field.widget, Select):
            field.widget.attrs['class'] = 'chosen-widget'
            # field.widget.attrs['style'] = 'width: 100%;'
            if disable_help_text:
                field.help_text = None


def construct_autocomplete_searchform(autocomplete_classname):
    """
    Construct a crispy form to display a search input field for list views.

    :param str autocomplete_classname: Name of the autocompletion registered with autocomplete_light
    :return: Crispy from instance
    """
    class SearchForm(Form):
        value = al.ChoiceField(
            label='',
            required=False,
            widget=al.TextWidget(autocomplete_classname)
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_id = 'default-search-form'
            self.helper.add_layout(
                FieldWithButtons(
                    'value',
                    StrictButton(
                        '<span class="glyphicon glyphicon-search"></span>',
                        css_class='btn-info btn-sm',
                        id='submit-search'
                    )
                )
            )

    return SearchForm()


# class classproperty(property):
#     def __get__(self, cls, owner):
#         return classmethod(self.fget).__get__(None, owner)()

# def construct_autocomplete_filtersearchform(model_class, search_field, user=None):
#     if user:
#         queryset = get_objects_for_model(user, model_class)
#     else:
#         queryset = model_class.objects.all()
#
#     class ListViewFilterAutocomplete(al.AutocompleteModelBase):
#         # find solution for dynamic search_fields (this way it registers globally)
#         search_fields = [search_field]
#         attrs = {'placeholder': 'Search yo'}
#         choices = queryset
#
#         def choices_for_request(self):
#             if user:
#                 self.choices = get_objects_for_model(user, model_class)
#             else:
#                 self.choices = model_class.objects.all()
#             return super().choices_for_request()
#
#     # try:
#     #     al.registry.unregister('ListViewFilterAutocomplete')
#     # except:
#     #     pass
#     ### CAUTION this is not thread save (registers for all requests/users) ###
#     al.register(model_class, ListViewFilterAutocomplete, name='ListViewFilterAutocomplete')
#     class SearchForm(Form):
#         value = al.ChoiceField(autocomplete='ListViewFilterAutocomplete', label='')
#         def __init__(self, *args, **kwargs):
#             super().__init__(*args, **kwargs)
#             self.helper = FormHelper()
#             self.helper.form_id = 'filter-search-form'
#     return SearchForm()
