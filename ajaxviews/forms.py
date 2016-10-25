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
            delete_success_url = form.opts.get(
                'delete_success_url', force_text(getattr(form.Meta, 'success_url', success_url)))
            delete_url += 'success_url=' + delete_success_url
        template = get_template(form.opts.get('form_actions_template', 'ajaxviews/_form_controls.html'))
        btn_group = template.render({
            'delete_url': delete_url,
            'success_url': force_text(success_url),
            'modal_form': form.opts.get('modal_form', False),
            'form_preview': form.opts.get('back_button', False),
            'delete_confirmation': form.opts.get('delete_confirmation', False),
            'form_cfg': json.dumps(form.form_cfg) if form.form_cfg else None,
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


class SimpleForm(Form):
    def __init__(self, *args, **kwargs):
        self._helper_instance = None
        # init_helper = kwargs.pop('init_helper', True)
        self.form_cfg = kwargs.pop('form_cfg', {})
        self.object = kwargs.pop('instance', None)
        self.model_data = kwargs.pop('model_data', None)
        self.user = kwargs.pop('user', None)
        self.opts = get_form_helper_attr(kwargs)
        success_message_ = kwargs.pop('success_message', None)
        init_chosen_widget_ = kwargs.pop('init_chosen_widget', False)
        init_date_widget_ = kwargs.pop('init_date_widget', False)
        kwargs.pop('related_obj_ids', None)
        super().__init__(*args, **kwargs)

        if init_chosen_widget_:
            init_chosen_widget(self.fields.items())
        if init_date_widget_:
            init_dateinput(self.fields.items())
        if success_message_:
            self.form_cfg['success_message'] = success_message_
            # self.fields['success_message'] = CharField(widget=HiddenInput(), required=False)
            # self.fields['success_message'].initial = success_message

        # if init_helper:
        #     self.init_helper()

    @property
    def helper(self):
        if self._helper_instance:
            return self._helper_instance
        if self.form_cfg:
            self.fields['form_cfg'] = CharField(widget=HiddenInput(), required=False)
            self.fields['form_cfg'].initial = json.dumps(self.form_cfg)
        helper = DefaultFormHelper(self)
        helper.form_action = self.opts.get('form_action', None)
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

    # def init_helper(self, init_chosen=True, form_actions=True):
    #     if init_chosen:
    #         init_chosen_widget(self.fields.items())
    #     self.helper = DefaultFormHelper(self)
    #     if form_actions:
    #         self.helper.append_form_actions()

    # def append_form_actions(self):
    #     self.helper.append_form_actions()

    # @classproperty
    # def headline(self):
    #     return getattr(self.Meta, 'headline', getattr(self.Meta, 'headline_full', ''))


class GenericModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self._helper_instance = None
        self.json_cache = kwargs.pop('json_cache', {})
        self.form_cfg = kwargs.pop('form_cfg', {})
        self.user = kwargs.pop('user', None)
        self.opts = get_form_helper_attr(kwargs)
        init_chosen_widget_ = kwargs.pop('init_chosen_widget', True)
        init_date_widget_ = kwargs.pop('init_date_widget', True)
        super().__init__(*args, **kwargs)

        for key, value in self.form_cfg.get('related_obj_ids', {}).copy().items():
            field_name = key.replace('_id', '')
            if field_name in self.fields:
                self.fields[field_name].initial = value
                del self.form_cfg['related_obj_ids'][key]

        if init_chosen_widget_:
            init_chosen_widget(self.fields.items())
        if init_date_widget_:
            init_dateinput(self.fields.items())

        for field_name, url_name in getattr(self.Meta, 'add_fields', {}).items():
            try:
                url = reverse(url_name)
            except NoReverseMatch:
                url = reverse(url_name, args=[self.instance.pk])
            # self.fields[field_name].label_suffix = ""  # suffix not supported by django-crispy-forms
            url += '?auto_select_field=' + field_name
            self.fields[field_name].label += """
                <a class="modal-link pull-right" href="{0}" style="margin-top: -3px; margin-left: 5px;">
                    <img src="{1}" width="15" height="15" alt="{2}"/>
                </a>""".format(url, static('admin/img/icon-addlink.svg'), 'Add')

    @property
    def helper(self):
        if self._helper_instance:
            return self._helper_instance
        if self.form_cfg:
            self.fields['form_cfg'] = CharField(widget=HiddenInput(), required=False)
            self.fields['form_cfg'].initial = json.dumps(self.form_cfg)
        helper = DefaultFormHelper(self)
        helper.form_action = self.opts.get('form_action', None)
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

    @property
    def cleaned_form_cfg(self):
        if 'form_cfg' in self.cleaned_data:
            return json.loads(self.cleaned_data['form_cfg'])
        return {}

    def render_form_actions(self):
        form = Form()
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
        if 'auto_select_field' in self.cleaned_form_cfg:
            self.json_cache['auto_select_choice'] = {
                'pk': instance.pk,
                'field': self.form_cfg['auto_select_field'],
                'text': str(instance),
            }
        return instance


def get_form_helper_attr(kwargs):
    return {
        'success_url': kwargs.pop('success_url', None),
        'form_action': kwargs.pop('form_action', None),
        'delete_url': kwargs.pop('delete_url', None),
        'modal_form': kwargs.pop('modal_form', False),
        'back_button': kwargs.pop('back_button', False),
        'save_button_name': kwargs.pop('save_button_name', 'Save'),
        'init_chosen_widget': kwargs.pop('init_chosen_widget', True),
        'init_date_widget': kwargs.pop('init_date_widget', True),
        'delete_confirmation': kwargs.pop('delete_confirmation', False),
        'form_actions_template': kwargs.pop('form_actions_template', 'ajaxviews/_form_controls.html'),
    }


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
