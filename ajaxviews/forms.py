import json

from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.admin.templatetags.admin_static import static
from django.forms import Form, ModelForm, CharField, HiddenInput

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import LayoutObject, Layout, Submit, HTML
from crispy_forms.utils import render_crispy_form, TEMPLATE_PACK
from django.template.loader import get_template
from django.utils.encoding import force_text

from .helpers import init_chosen_widget, init_dateinput


class DefaultFormActions(LayoutObject):
    # noinspection PyUnusedLocal, PyMethodMayBeStatic
    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK):
        success_url = form.opts.get('success_url', '')
        delete_url = form.opts.get('delete_url', '')
        if delete_url:
            delete_url += '&' if '?' in delete_url else '?'
            delete_success_url = form.opts.get('delete_success_url', '')
            if not delete_success_url and hasattr(form, 'Meta') and hasattr(form.Meta, 'success_url'):
                delete_success_url = force_text(getattr(form.Meta, 'success_url'))
            if not delete_success_url:
                delete_success_url = force_text(success_url)
            delete_url += 'success_url=' + delete_success_url
        template = get_template(form.opts.get('form_actions_template', 'ajaxviews/_form_controls.html'))
        btn_group = template.render({
            'delete_url': delete_url,
            'success_url': force_text(success_url),
            'modal_form': form.opts.get('modal_form', False),
            'form_preview': True if form.opts.get('preview_stage', 0) == 1 else False,
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs = {'data-async': ''}

    def append_form_actions(self):
        self.layout.append(DefaultFormActions())

    def add_form_actions_only(self):
        self.form_tag = False
        self.add_layout(Layout(DefaultFormActions()))


# noinspection PyUnresolvedReferences
class FormMixin:
    def __init__(self, *args, **kwargs):
        self._helper_instance = None
        self.form_cfg = kwargs.pop('form_cfg', {})
        self.user = kwargs.pop('user', None)
        self.opts = get_form_helper_kwargs(kwargs)
        super().__init__(*args, **kwargs)

    @property
    def helper(self):
        if self._helper_instance is not None:
            return self._helper_instance
        if self.form_cfg:
            self.fields['form_cfg'] = CharField(widget=HiddenInput(), required=False)
            self.fields['form_cfg'].initial = json.dumps(self.form_cfg)
        helper = DefaultFormHelper(self)
        if 'form_action' in self.opts:
            helper.form_action = self.opts['form_action']
        helper.render_hidden_fields = True
        helper.append_form_actions()
        self._helper_instance = helper
        return helper

    @property
    def layout(self):
        return self.helper.layout

    @layout.setter
    def layout(self, layout):
        self.helper.add_layout(layout)
        self.helper.append_form_actions()


class SimpleForm(FormMixin, Form):
    def __init__(self, *args, **kwargs):
        self.object = kwargs.pop('instance', None)
        # self.model_data = kwargs.pop('model_data', None)
        self.model_form = kwargs.pop('model_form', None)
        success_message = kwargs.pop('success_message', None)
        super().__init__(*args, **kwargs)

        if self.model_data is not None:
            print('- ' * 30 + 'model data' + ' -' * 30)
            print(self.opts.get('model_data'))
            self.form_cfg['model_form'] = self.opts.get('model_data', None)
        if success_message is not None:
            self.form_cfg['success_message'] = success_message
        if self.opts.get('init_chosen_widget', True):
            init_chosen_widget(self.fields.items())
        if self.opts.get('init_date_widget', True):
            init_dateinput(self.fields.items())


class GenericModelForm(FormMixin, ModelForm):
    field_label_addon = """<a class="modal-link form-add-link" href="{0}"><img src="{1}" alt="{2}"/></a>"""

    def __init__(self, *args, **kwargs):
        self.json_cache = kwargs.pop('json_cache', {})
        # model_data = kwargs.pop('model_data', None)
        super().__init__(*args, **kwargs)

        # if model_data:
        #     self.form_cfg['model_data'] = model_data

        for key, value in self.form_cfg.get('related_obj_ids', {}).copy().items():
            field_name = key.replace('_id', '')
            if field_name in self.fields:
                self.fields[field_name].initial = value
                del self.form_cfg['related_obj_ids'][key]

        if self.opts.get('init_chosen_widget', True):
            init_chosen_widget(self.fields.items())
        if self.opts.get('init_date_widget', True):
            init_dateinput(self.fields.items())

        for field_name, url_name in getattr(self.Meta, 'add_fields', {}).items():
            try:
                url = reverse(url_name)
            except NoReverseMatch:
                url = reverse(url_name, args=[self.instance.pk])
            # self.fields[field_name].label_suffix = ""  # suffix not supported by django-crispy-forms
            url += '?auto_select_field=' + field_name
            self.fields[field_name].label += self.field_label_addon.format(
                url, static('admin/img/icon-addlink.svg'), 'Add')

    @property
    def cleaned_form_cfg(self):
        if 'form_cfg' in self.cleaned_data:
            return json.loads(self.cleaned_data['form_cfg'])
        return {}

    def render_form_actions(self):
        form = Form()
        form.opts = self.opts
        form.helper = DefaultFormHelper(self)
        form.helper.add_form_actions_only()
        return render_crispy_form(form)

    def get_related_obj(self, model, key=None):
        related_obj_dict = self.cleaned_form_cfg.get('related_obj_ids', None)
        if not related_obj_dict:
            return None
        if key:
            related_obj_id = related_obj_dict[key]
        else:
            related_obj_id = list(related_obj_dict.values())[0]
        return model.objects.get(pk=int(related_obj_id))

    def save(self, commit=True):
        instance = super().save(commit)
        if commit and 'auto_select_field' in self.cleaned_form_cfg:
            self.json_cache['auto_select_choice'] = {
                'pk': instance.pk,
                'field': self.form_cfg['auto_select_field'],
                'text': str(instance),
            }
        return instance


def get_form_helper_kwargs(kwargs):
    form_kwargs = [
        'success_url',
        'form_action',
        'delete_url',
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
    form_opts = {}
    for key in list(kwargs):
        if key in form_kwargs:
            form_opts[key] = kwargs.pop(key)
    return form_opts


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
