from django.conf import settings as django_settings


# noinspection PyPep8Naming
class LazySettings:
    @property
    def REQUIRE_MAIN_NAME(self):
        return getattr(django_settings, 'REQUIRE_MAIN_NAME', 'main')

    @property
    def DEFAULT_PAGINATE_BY(self):
        return getattr(django_settings, 'DEFAULT_PAGINATE_BY', 30)

    @property
    def FILTER_SEARCH_INPUT_BY(self):
        return getattr(django_settings, 'FILTER_SEARCH_INPUT_BY', 10)

    @property
    def AUTO_PAGE_SIZE(self):
        return getattr(django_settings, 'AUTO_PAGE_SIZE', True)

    @property
    def AUTO_FORM_HEADLINE(self):
        return getattr(django_settings, 'AUTO_FORM_HEADLINE', True)

    @property
    def CREATE_FORM_HEADLINE_PREFIX(self):
        return getattr(django_settings, 'CREATE_FORM_HEADLINE_PREFIX', 'Add')

    @property
    def UPDATE_FORM_HEADLINE_PREFIX(self):
        return getattr(django_settings, 'UPDATE_FORM_HEADLINE_PREFIX', 'Edit')

    @property
    def FORM_RELATED_OBJECT_IDS(self):
        return getattr(django_settings, 'FORM_RELATED_OBJECT_IDS', True)

    @property
    def GENERIC_FORM_BASE_TEMPLATE(self):
        return getattr(django_settings, 'GENERIC_FORM_BASE_TEMPLATE', 'ajaxviews/generic_form.html')

    @property
    def AUTO_DELETE_URL(self):
        return getattr(django_settings, 'AUTO_DELETE_URL', True)

    @property
    def FORM_DELETE_CONFIRMATION(self):
        return getattr(django_settings, 'FORM_DELETE_CONFIRMATION', True)

    @property
    def AUTO_SUCCESS_URL(self):
        return getattr(django_settings, 'AUTO_SUCCESS_URL', True)

settings = LazySettings()
