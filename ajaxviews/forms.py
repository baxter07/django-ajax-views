import json

from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.admin.templatetags.admin_static import static
from django.forms import Form, ModelForm, CharField, HiddenInput

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import LayoutObject, Layout, Submit, HTML
from crispy_forms.utils import render_crispy_form, TEMPLATE_PACK
from django.template.loader import get_template

from .helpers import classproperty, init_chosen_widget, init_dateinput


class DefaultFormActions(LayoutObject):
    def __init__(self, **kwargs):
        self.opts = kwargs.copy()
        self.save_button_name = kwargs.pop('save_button_name', 'Save')
        self.success_url = kwargs.pop('success_url', '#')
        self.delete_url = kwargs.pop('delete_url', None)
        self.modal_form = kwargs.pop('modal_form', False)
        self.delete_confirmation = kwargs.pop('delete_confirmation', False)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK):
        # preview_back_class = ''
        # cancel_button_name = 'Cancel'
        # if self.back_button:
        #     preview_back_class = ' preview-back'
        #     cancel_button_name = 'Back'
        #
        # cancel_attr = 'href="{0}"'.format(self.success_url)
        #
        # if not self.back_button and self.modal_form:
        #     cancel_button_name = 'Close'
        #     cancel_attr = 'data-dismiss="modal"'
        #
        # btn_group = """<a role="button" class="btn btn-default cancel-btn{0}" {1}>
        #                  {2}
        #                </a>""".format(preview_back_class, cancel_attr, cancel_button_name)
        success_url = self.opts.get('success_url', '')
        delete_url = self.opts.get('delete_url', '')
        if delete_url:
            if success_url and success_url != '#':
                delete_url += '&' if '?' in delete_url else '?'
                delete_url += 'success_url=' + success_url
            # btn_group += """<a role="button" class="btn btn-danger pull-right" data-toggle="confirmation" href="{0}">
            #                   Delete
            #                 </a>""".format(self.delete_url)

        template = get_template('ajaxviews/_form_controls.html')
        btn_group = template.render({
            'success_url': success_url,
            'delete_url': delete_url,
            'modal_form': self.opts.get('modal_form', False),
            'form_preview': self.opts.get('back_button', False),
            'delete_confirmation': self.opts.get('delete_confirmation', False),
        })

        layout_object = FormActions(
            Submit('save', self.save_button_name),
            HTML(btn_group),
            style='margin-bottom: 0;'
        )
        return layout_object.render(form, form_style, context)


class DefaultFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        form_action = kwargs.pop('form_action', None)
        self.form_actions_attr = kwargs.copy()
        kwargs = {}
        super().__init__(*args, **kwargs)

        if form_action:
            self.form_action = form_action
        self.attrs = {'data-async': ''}
        self.render_hidden_fields = True

    def append_form_actions(self):
        self.layout.append(DefaultFormActions(**self.form_actions_attr))

    def add_form_actions_only(self):
        self.form_tag = False
        self.add_layout(Layout(DefaultFormActions(**self.form_actions_attr)))


class SimpleForm(Form):
    def __init__(self, *args, **kwargs):
        init_helper = kwargs.pop('init_helper', True)
        self.object = kwargs.pop('instance', None)
        self.model_data = kwargs.pop('model_data', None)
        self.user = kwargs.pop('user', None)
        self.helper_kwargs = get_form_helper_attr(kwargs)
        success_message = kwargs.pop('success_message', None)
        kwargs.pop('related_obj_ids', None)
        super().__init__(*args, **kwargs)

        if success_message:
            self.fields['success_message'] = CharField(widget=HiddenInput(), required=False)
            self.fields['success_message'].initial = success_message

        if init_helper:
            self.init_helper()

    def init_helper(self, init_chosen=True, form_actions=True):
        if init_chosen:
            init_chosen_widget(self.fields.items())
        self.helper = DefaultFormHelper(self, **self.helper_kwargs)
        if form_actions:
            self.helper.append_form_actions()

    def append_form_actions(self):
        self.helper.append_form_actions()

    @classproperty
    def headline(self):
        return getattr(self.Meta, 'headline', getattr(self.Meta, 'headline_full', ''))


class GenericModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = None
        self.form_cfg = kwargs.pop('form_cfg', {})
        self.user = kwargs.pop('user', None)
        self.helper_kwargs = get_form_helper_attr(kwargs)
        init_helper = kwargs.pop('init_helper', True)
        # modal_add_fields = kwargs.pop('modal_add_fields', True)
        # kwargs.setdefault('label_suffix', 'yoyooooooooo')
        super().__init__(*args, **kwargs)

        if 'related_obj_ids' in self.form_cfg:
            # for key, value in list(self.form_cfg['related_obj_ids'].items()):
            for key, value in self.form_cfg['related_obj_ids'].items():
                field_name = key.replace('_id', '')
                if field_name in self.fields:
                    self.fields[field_name].initial = value
                    del self.form_cfg['related_obj_ids'][key]
        if self.form_cfg:
            self.fields['form_cfg'] = CharField(widget=HiddenInput(), required=False)
            self.fields['form_cfg'].initial = json.dumps(self.form_cfg)

        if 'select_field' in kwargs.get('data', {}):
            self.fields[kwargs['data'].get('select_field')].initial = kwargs['data'].get('select_pk')

        self._init_modal_add_fields()

        if init_helper:
            self.init_helper()

    # @property
    # def helper(self):
    #     print('------------------------------------------- init form helper ---------------------------------------')
    #     return DefaultFormHelper(self, **self.helper_kwargs)

    def init_helper(self, form_actions=True):
        # self._init_modal_fields()
        # if hasattr(self.Meta, 'modal_fields'):
        #     self._init_modal_fields()

        if self.helper_kwargs.pop('init_chosen_widget', True):
            init_chosen_widget(self.fields.items())
        init_dateinput(self.fields.items())

        self.helper = DefaultFormHelper(self, **self.helper_kwargs)
        # self.helper.render_hidden_fields = True

        if self.form_cfg:
            self.helper.layout.append(
                '<input name="form_cfg" value="{}" type="hidden">'.format(json.dumps(self.form_cfg))
            )
        if form_actions:
            self.append_form_actions()

    def _init_modal_add_fields(self):
        for field_name, url_name in getattr(self.Meta, 'add_fields', {}).items():
            try:
                url = reverse(url_name)
            except NoReverseMatch:
                url = reverse(url_name, args=[self.instance.pk])
            self.fields[field_name].help_text = '<b>test-{}</b>'.format(url)
            self.fields[field_name].label += """
                <a class="modal-link pull-right" href="{0}" style="margin-top: -3px; margin-left: 5px;">
                    <img src="{1}" width="15" height="15" alt="{2}"/>
                </a>""".format(url, static('admin/img/icon-addlink.svg'), 'Add')

    def custom_success_url(self, url):
        self.helper_kwargs['success_url'] = url
        self.form_cfg['success_url'] = url
        # self.fields['success_url'] = CharField(widget=HiddenInput(), required=False, initial=url)

    def append_form_actions(self):
        self.helper.append_form_actions()
        # if 'related_obj_ids' in self.fields:
        #     self.helper.layout.append('related_obj_ids')
        # if 'success_url' in self.fields:
        #     self.helper.layout.append('success_url')

    def render_form_actions(self):
        form = Form()
        form.helper = DefaultFormHelper(**self.helper_kwargs.copy())
        form.helper.add_form_actions_only()
        return render_crispy_form(form)

    @property
    def get_form_cfg(self):
        if 'form_cfg' in self.cleaned_data:
            return json.loads(self.cleaned_data['form_cfg'])
        return {}

    def get_related_obj(self, model, key=None):
        related_obj_dict = self.get_form_cfg.get('related_obj_ids', None)
        if not related_obj_dict:
            return None
        if key:
            related_obj_id = related_obj_dict[key]
        else:
            related_obj_id = list(related_obj_dict.values())[0]
        return model.objects.get(pk=int(related_obj_id))

    @classproperty
    def headline(self):
        return getattr(self.Meta, 'headline', getattr(self.Meta, 'headline_full', ''))


def get_form_helper_attr(kwargs):
    return {
        'save_button_name': kwargs.pop('save_button_name', 'Save'),
        'success_url': kwargs.pop('success_url', None),
        'delete_url': kwargs.pop('delete_url', None),
        'form_action': kwargs.pop('form_action', None),
        'modal_form': kwargs.pop('modal_form', False),
        'back_button': kwargs.pop('back_button', False),
        'delete_confirmation': kwargs.pop('delete_confirmation', False),
        'init_chosen_widget': kwargs.pop('init_chosen_widget', True),
    }

# if hasattr(self.Meta, 'right_column'):
#     left_fields, right_fields = [], []
#     right_column_fields = getattr(self.Meta, 'right_column')
#     for field_name, field in self.fields.items():
#         if field_name in right_column_fields:
#             right_fields.append(Field(field_name))
#         else:
#             left_fields.append(Field(field_name))
#     self.helper.add_layout(
#         Layout(
#             Div(
#                 Div(*left_fields, css_class='col-md-6'),
#                 Div(*right_fields, css_class='col-md-6'),
#                 css_class='row'
#             ),
#             self.helper.layout[-1][0]
#         )
#     )

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
