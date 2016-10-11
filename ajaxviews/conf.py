from django.conf import settings as django_settings


# noinspection PyPep8Naming
class LazySettings:
    @property
    def DEFAULT_PAGINATE_BY(self):
        return getattr(django_settings, 'DEFAULT_PAGINATE_BY', 30)

    @property
    def FILTER_SEARCH_INPUT_BY(self):
        return getattr(django_settings, 'FILTER_SEARCH_INPUT_BY', 10)

    @property
    def REQUIRE_MAIN_NAME(self):
        return getattr(django_settings, 'REQUIRE_MAIN_NAME', 'main')

    @property
    def FORM_GENERIC_HEADLINE(self):
        return getattr(django_settings, 'FORM_GENERIC_HEADLINE', True)

    @property
    def CREATE_FORM_HEADLINE_PREFIX(self):
        return getattr(django_settings, 'CREATE_FORM_HEADLINE_PREFIX', 'Add')

    @property
    def UPDATE_FORM_HEADLINE_PREFIX(self):
        return getattr(django_settings, 'UPDATE_FORM_HEADLINE_PREFIX', 'Edit')

    @property
    def GENERIC_FORM_BASE_TEMPLATE(self):
        return getattr(django_settings, 'GENERIC_FORM_BASE_TEMPLATE', None)

    @property
    def FORM_RELATED_OBJECT_IDS(self):
        return getattr(django_settings, 'FORM_RELATED_OBJECT_IDS', False)

    @property
    def FORM_DELETE_CONFIRMATION(self):
        return getattr(django_settings, 'FORM_DELETE_CONFIRMATION', False)

settings = LazySettings()
