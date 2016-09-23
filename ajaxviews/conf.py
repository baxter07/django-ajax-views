from django.conf import settings as django_settings


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

settings = LazySettings()
