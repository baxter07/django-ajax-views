import json

from django.core.urlresolvers import reverse
from django.contrib.admin.templatetags.admin_static import static
from django.forms import Form, ModelForm, CharField, HiddenInput

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import LayoutObject, Layout, Submit, HTML
from crispy_forms.utils import render_crispy_form, TEMPLATE_PACK

from .helpers import classproperty, init_chosen_widget, init_dateinput


def get_form_helper_attr(kwargs):
    return {
        'save_button_name': kwargs.pop('save_button_name', 'Save'),
        'success_url': kwargs.pop('success_url', None),
        'delete_url': kwargs.pop('delete_url', None),
        'form_action': kwargs.pop('form_action', None),
        'modal_form': kwargs.pop('modal_form', False),
        'back_button': kwargs.pop('back_button', False),
        'init_chosen_widget': kwargs.pop('init_chosen_widget', True),
    }


class DefaultFormActions(LayoutObject):
    def __init__(self, **kwargs):
        self.save_button_name = kwargs.pop('save_button_name', 'Save')
        self.success_url = kwargs.pop('success_url', '#')
        self.delete_url = kwargs.pop('delete_url', None)
        self.modal_form = kwargs.pop('modal_form', False)
        self.back_button = kwargs.pop('back_button', False)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK):
        preview_back_class = ''
        cancel_button_name = 'Cancel'
        if self.back_button:
            preview_back_class = ' preview-back'
            cancel_button_name = 'Back'

        cancel_attr = 'href="{0}"'.format(self.success_url)
        
        if not self.back_button and self.modal_form:
            cancel_button_name = 'Close'
            cancel_attr = 'data-dismiss="modal"'

        btn_group = """<a role="button" class="btn btn-default cancel-btn{0}" {1}>
                         {2}
                       </a>""".format(preview_back_class, cancel_attr, cancel_button_name)

        if self.delete_url:
            if self.success_url and self.success_url != '#':
                self.delete_url += '&' if '?' in self.delete_url else '?'
                self.delete_url += 'success_url=' + self.success_url
            btn_group += """<a role="button" class="btn btn-danger pull-right" data-toggle="confirmation" href="{0}">
                              Delete
                            </a>""".format(self.delete_url)

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

    def append_form_actions(self):
        self.layout.append(
            DefaultFormActions(**self.form_actions_attr)
        )

    def add_form_actions_only(self):
        self.form_tag = False
        self.add_layout(
            Layout(DefaultFormActions(**self.form_actions_attr))
        )


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
        if hasattr(self.Meta, 'headline'):
            return getattr(self.Meta, 'headline')
        elif hasattr(self.Meta, 'headline_full'):
            return getattr(self.Meta, 'headline_full')
        return None


class GenericModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.helper = None
        init_helper = kwargs.pop('init_helper', True)
        related_obj_ids = kwargs.pop('related_obj_ids', None)
        self.user = kwargs.pop('user', None)
        self.helper_kwargs = get_form_helper_attr(kwargs)
        super().__init__(*args, **kwargs)

        if related_obj_ids:
            for key, value in list(related_obj_ids.items()):
                field_name = key.replace('_id', '')
                if field_name in self.fields:
                    self.fields[field_name].initial = value
                    del related_obj_ids[key]
            if related_obj_ids:
                self.fields['related_obj_ids'] = CharField(widget=HiddenInput(), required=False)
                self.fields['related_obj_ids'].initial = json.dumps(related_obj_ids)

        if init_helper:
            self.init_helper()

    def init_helper(self, form_actions=True):
        if hasattr(self.Meta, 'modal_fields'):
            self._init_modal_fields()

        if self.helper_kwargs.pop('init_chosen_widget', True):
            init_chosen_widget(self.fields.items())
        init_dateinput(self.fields.items())

        self.helper = DefaultFormHelper(self, **self.helper_kwargs)
        self.helper.render_hidden_fields = True

        if form_actions:
            self.append_form_actions()

    def _init_modal_fields(self):
        for field_name, url_name in getattr(self.Meta, 'modal_fields').items():
            try:
                url = reverse(url_name)
            except:
                try:
                    # TODO document that the id of the current model is used for generic add fields with parameter
                    url = reverse(url_name, args=(self.instance.pk,))
                except:
                    url = None
            if url:
                self.fields[field_name].label += """ <a class="modal-link" href="{0}">
                                                        <img src="{1}" width="15" height="15" alt="{2}"/>
                                                     </a>""".format(url, static('admin/img/icon_addlink.gif'), 'Add')

    def custom_success_url(self, url):
        self.helper_kwargs['success_url'] = url
        self.fields['success_url'] = CharField(widget=HiddenInput(), required=False, initial=url)

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
    def related_ids(self):
        try:
            return json.loads(self.cleaned_data['related_obj_ids'])
        except:
            return {}

    def get_related_obj(self, model, key=None):
        related_obj_dict = self.related_ids
        if not related_obj_dict:
            return None
        if key:
            if key not in related_obj_dict:
                return None
            related_obj_id = related_obj_dict[key]
        else:
            related_obj_id = list(related_obj_dict.values())[0]
        return model.objects.get(pk=int(related_obj_id))

    @classproperty
    def headline(self):
        if hasattr(self.Meta, 'headline'):
            return getattr(self.Meta, 'headline')
        elif hasattr(self.Meta, 'headline_full'):
            return getattr(self.Meta, 'headline_full')
        return None


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
