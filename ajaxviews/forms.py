import json

from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.admin.templatetags.admin_static import static
from django.template import Template, Context
from django.utils.encoding import force_text
from django.template.loader import get_template
from django.forms.models import BaseModelFormSet
from django.forms import Form, ModelForm, CharField, HiddenInput

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import LayoutObject, Layout, Submit, HTML
from crispy_forms.utils import render_crispy_form, TEMPLATE_PACK

from .helpers import init_chosen_widget, init_dateinput


class DefaultFormActions(LayoutObject):
    """
    Crispy layout object that renders form actions depending on options defined in ``form.opts`` property.

    Keyword arguments available in ``opts``:

    :ivar str success_url: Url to redirect to on successful form save.
    :ivar str delete_url: Delete view that's requested on form delete.
    :ivar str delete_success_url: Url to redirect view on successful form deletion.
    :ivar str form_actions_template: Template to render form actions in. Default: ``'ajaxviews/_form_controls.html'``
    :ivar int preview_stage: If form preview is displayed render a back button.
    :ivar bool modal_form: True if form is displayed in a bootrap modal. Default: ``False``
    :ivar bool delete_confirmation: Display a `bootstrap confirmation <http://bootstrap-confirmation.js.org/>`_
        popover if delete button is clicked.
    :ivar dict form_cfg: Additional data needed to process form save passed through a hidden input field. Dictionary
        is stringified and automatically parsed again when calling :func:`FormMixin.cleaned_form_cfg`.
    """
    # noinspection PyUnusedLocal, PyMethodMayBeStatic
    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK):
        success_url = form.opts.get('success_url', '')
        delete_url = form.opts.get('delete_url', '')
        if delete_url:
            delete_url += '&' if '?' in delete_url else '?'
            delete_url += 'success_url=' + force_text(form.opts.get('delete_success_url', success_url))
        template = get_template(form.opts.get('form_actions_template', 'ajaxviews/_form_controls.html'))
        btn_group = template.render({
            'delete_url': delete_url,
            'success_url': force_text(success_url),
            'modal_form': form.opts.get('modal_form', False),
            'form_preview': form.opts.get('preview_stage', False),
            'delete_confirmation': form.opts.get('delete_confirmation', False),
            'form_cfg': json.dumps(form.form_cfg) if getattr(form, 'form_cfg', None) else None,
        })
        layout_object = FormActions(
            Submit('save', form.opts.get('save_button_name', 'Save')),
            HTML(btn_group),
            style='margin-bottom: 0;'
        )
        return layout_object.render(form, form_style, context)


class DefaultFormHelper(FormHelper):
    """
    Crispy form helper used to define default form action control.

    A ``data-async`` html property is added to the form tag.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs = {'data-async': ''}

    def append_form_actions(self):
        """
        Append form actions to the current layout.
        """
        self.layout.append(DefaultFormActions())

    def add_form_actions_only(self):
        """
        Disable the form tag and add form actions only to the current layout.
        """
        self.form_tag = False
        self.add_layout(Layout(DefaultFormActions()))


# noinspection PyUnresolvedReferences
class FormMixin:
    """
    Mixin that handels instantiation of crispy form helper and options passed in the form's init kwargs.

    :ivar dict opts: 
    """
    form_kwargs = [
        'success_url',
        'form_action',
        'delete_url',
        'delete_success_url',
        'modal_form',
        'preview_stage',
        'model_data',
        'preview_data',
        'save_button_name',
        'init_chosen_widget',
        'init_date_widget',
        'delete_confirmation',
        'form_actions_template',
    ]

    def __init__(self, *args, **kwargs):
        self._helper_instance = None
        self.form_cfg = kwargs.pop('form_cfg', {})
        self.user = kwargs.pop('user', None)
        self.opts = {}
        for key in list(kwargs):
            if key in self.form_kwargs:
                self.opts[key] = kwargs.pop(key)
        super().__init__(*args, **kwargs)

    @property
    def helper(self):
        """
        The :class:`DefaultFormHelper` is instantiated only once when this helper property is accessed first.

        Assign your own form helper if you want to override the default behavior.

        This renders hidden fields and appends form actions by default.

        :return: Form helper instance
        """
        if self._helper_instance is not None:
            return self._helper_instance
        if self.form_cfg:
            self.fields['form_cfg'] = CharField(widget=HiddenInput(), required=False)
            self.fields['form_cfg'].initial = json.dumps(self.form_cfg)
        try:
            self.init_add_fields()
        except AttributeError:
            pass
        helper = DefaultFormHelper(self)
        if 'form_action' in self.opts:
            helper.form_action = self.opts['form_action']
        helper.render_hidden_fields = True
        helper.append_form_actions()
        self._helper_instance = helper
        return helper

    @helper.setter
    def helper(self, helper):
        self._helper_instance = helper

    @property
    def cleaned_form_cfg(self):
        """
        Loads the stringified ``form_cfg`` in ``cleaned_data`` to return a python dictionary object.

        :return: form cfg dictionary
        """
        if 'form_cfg' in self.cleaned_data:
            return json.loads(self.cleaned_data['form_cfg'])
        return {}

    @property
    def layout(self):
        """
        Get or set the crispy form helper layout object. If you set a new layout the form actions are
        appended automatically.
        """
        return self.helper.layout

    @layout.setter
    def layout(self, layout):
        self.helper.add_layout(layout)
        self.helper.append_form_actions()


class SimpleForm(FormMixin, Form):
    """
    Generic form for use without a corresponding model. Also used to display a preview before saving a form.

    :ivar object object: Model instance of the preview forms first stage.
    :ivar dict model_data: Cleaned data of the preview forms second stage.
    """
    def __init__(self, *args, **kwargs):
        self.object = kwargs.pop('instance', None)
        self.model_data = kwargs.pop('model_data', None)
        success_message = kwargs.pop('success_message', None)
        super().__init__(*args, **kwargs)

        if success_message is not None:
            self.form_cfg['success_message'] = success_message
        if self.opts.get('init_chosen_widget', True):
            init_chosen_widget(self.fields.items())
        if self.opts.get('init_date_widget', True):
            init_dateinput(self.fields.items())


class GenericModelForm(FormMixin, ModelForm):
    """
    Generic form for use with a corresponding model.
    """
    field_label_addon = """<a class="modal-link form-add-link" href="{0}"><img src="{1}" alt="{2}"/></a>"""

    def __init__(self, *args, **kwargs):
        self.json_cache = kwargs.pop('json_cache', {})
        super().__init__(*args, **kwargs)

        for key, value in self.form_cfg.get('related_obj_ids', {}).copy().items():
            field_name = key.replace('_id', '')
            if field_name in self.fields:
                self.fields[field_name].initial = value
                del self.form_cfg['related_obj_ids'][key]

        if self.opts.get('init_chosen_widget', True):
            init_chosen_widget(self.fields.items())
        if self.opts.get('init_date_widget', True):
            init_dateinput(self.fields.items())

    def init_add_fields(self):
        for field_name, url_name in getattr(self.Meta, 'add_fields', {}).items():
            try:
                url = reverse(url_name)
            except NoReverseMatch:
                url = reverse(url_name, args=[self.instance.pk])
            # self.fields[field_name].label_suffix = ""  # suffix not supported by django-crispy-forms
            url += '?auto_select_field=' + field_name
            self.fields[field_name].label += self.field_label_addon.format(
                url, static('admin/img/icon-addlink.svg'), 'Add'
            )

    def render_form_actions(self):
        form = Form()
        form.opts = self.opts
        form.helper = DefaultFormHelper(self)
        form.helper.add_form_actions_only()
        return render_crispy_form(form)

    def get_related_obj(self, model, key=None):
        """
        Get model instance with pk of related model from the calling view.

        :param model: Django model class.
        :param key: Keyword argument to get the value used to retrieve the model instance. If not specified it
            expects a single key in ``related_obj_ids`` that's used.
        :return: Model instance.
        """
        related_obj_dict = self.cleaned_form_cfg.get('related_obj_ids', None)
        if not related_obj_dict:
            return None
        if key:
            related_obj_id = related_obj_dict[key]
        else:
            related_obj_id = list(related_obj_dict.values())[0]
        return model.objects.get(pk=int(related_obj_id))

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and 'auto_select_field' in self.cleaned_form_cfg:
            self.json_cache['auto_select_choice'] = {
                'pk': instance.pk,
                'field': self.form_cfg['auto_select_field'],
                'text': str(instance),
            }
        return instance


class ModelFormSet(BaseModelFormSet):
    """
    Use this form to render form actions at the bottom of the formset.

    :var str form_actions_template: Template to render save and cancel buttons. Be sure to use
        the ``{{ success_url }}`` tag for your cancel button if you want to override this template.
    """
    form_actions_template = """
        <input name="save" class="btn btn-primary" type="submit" value="Save">
        <a role="button" class="btn btn-default cancel-btn" href="{{ success_url }}">Cancel</a>
    """

    def __init__(self, *args, **kwargs):
        self._success_url = kwargs.pop('success_url', None)
        super().__init__(*args, **kwargs)

    def render_form_actions(self, **kwargs):
        kwargs['success_url'] = self._success_url
        return Template(self.form_actions_template).render(Context(kwargs))


# helper.form_tag = False
# helper.layout = Layout(
#     TabHolder(
#         Tab(
#             'Basic Information',
#             'first_name',
#             'last_name'
#         ),
#         Tab(
#             'Address',
#             'address1',
#             'address2',
#         ),
#         Tab(
#             'Contact',
#             'email',
#             'mobile',
#         )
#     )
# )

# from djmoney.forms.widgets import MoneyWidget
# class CustomMoneyWidget(MoneyWidget):
#     def format_output(self, rendered_widgets):
#         return ('<div class="row">'
#                     '<div class="col-xs-6 col-sm-10">%s</div>'
#                     '<div class="col-xs-6 col-sm-2">%s</div>'
#                 '</div>') % tuple(rendered_widgets)

# class BookingForm(forms.ModelForm):
#     ...
#     def __init__(self, *args, **kwargs):
#         super(BookingForm, self).__init__(*args, **kwargs)
#         amount, currency = self.fields['amount'].fields
#         self.fields['amount'].widget = CustomMoneyWidget(
#             amount_widget=amount.widget, currency_widget=currency.widget)

# <a class="modal-link pull-right" href="{0}" style="margin-top: -3px; margin-left: 5px;">
#   <img src="{1}" width="15" height="15" alt="{2}"/>
# </a>
