import autocomplete_light.shortcuts as al
from django.forms import Form, Select, SelectMultiple, DateInput, DateTimeInput

from guardian.shortcuts import assign_perm, remove_perm, get_perms_for_model, get_objects_for_user
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FieldWithButtons, StrictButton


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


def get_objects_for_model(user, model, perm_prefix='access_'):
    package, module = model.__module__.split('.')

    for perm in get_perms_for_model(model):
        if perm_prefix in perm.codename:
            return get_objects_for_user(user, package + '.' + perm.codename)
    return None


def get_model_perm(user, model, perm_prefix='access_'):
    group_permissions = user.groups.first().permissions.all()
    package, module = model.__module__.split('.')

    for perm in get_perms_for_model(model):
        if perm_prefix in perm.codename and perm in group_permissions:
            return package + '.' + perm.codename
    return None


def assign_obj_perm(user, obj):
    permission = get_model_perm(user, obj.__class__)
    if not permission:
        raise Exception('No permissions to save object.')
    if not user.has_perm(permission, obj):
        assign_perm(permission, user, obj)
        return True
    return False


def remove_obj_perm(user, obj):
    permission = get_model_perm(user, obj.__class__)
    if not permission:
        raise Exception('No permissions to remove object.')
    if user.has_perm(permission, obj):
        remove_perm(permission, user, obj)
        return True
    return False


class DateWidget(DateInput):
    def render(self, name, value, attrs=None):
        html_input = super().render(name, value, attrs)
        return """<div class="input-group date">{0}
                    <div class="input-group-addon">
                      <span class="glyphicon glyphicon-calendar"></span>
                    </div>
                  </div>
               """.format(html_input)


def init_dateinput(field_items):
    for name, field in field_items:
        if isinstance(field.widget, DateInput) or isinstance(field.widget, DateTimeInput):
            field.widget = DateWidget()
            field.widget.attrs['class'] = 'dateinput'
            # field.widget.attrs['data-date-format'] = 'yyyy-mm-dd'


def init_chosen_widget(field_items):
    for name, field in field_items:
        if isinstance(field.widget, SelectMultiple) or isinstance(field.widget, Select):
            field.widget.attrs['class'] = 'chosen-widget'
            # field.widget.attrs['style'] = 'width: 100%;'
            # TODO provide option to use help_text, this disables it for all SelectMultiple and Select fields
            field.help_text = None


def construct_autocomplete_searchform(autocomplete_classname):
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


# def construct_autocomplete_filtersearchform(model_class, search_field, user=None):
#     if user:
#         queryset = get_objects_for_model(user, model_class)
#     else:
#         queryset = model_class.objects.all()

#     class ListViewFilterAutocomplete(al.AutocompleteModelBase):
#         # find solution for dynamic search_fields (this way it registers globally)
#         search_fields = [search_field]
#         attrs = {'placeholder': 'Search yo'}
#         choices = queryset

#         def choices_for_request(self):
#             if user:
#                 self.choices = get_objects_for_model(user, model_class)
#             else:
#                 self.choices = model_class.objects.all()
#             return super().choices_for_request()

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
