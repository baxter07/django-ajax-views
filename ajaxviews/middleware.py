import json

from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.template.loader import get_template
from django.core.serializers.json import DjangoJSONEncoder

from .conf import settings


class AjaxMiddleware:
    def process_response(self, request, response):
        if not request.is_ajax():
            _content = force_text(response.content, encoding=response.charset)
            if '</body>' not in _content:
                raise Exception('No body tag found in html response.')

            template = get_template('ajaxviews/_middleware.html')
            json_cfg = mark_safe(json.dumps(
                    response.context_data.get('json_cfg', {}),
                    cls=DjangoJSONEncoder
            ))
            html = template.render({
                'json_cfg': json_cfg,
                'main_name': settings.REQUIRE_MAIN_NAME,
            })

            response.content = response.make_bytes(_content.replace('</body>', html))
            if response.get('Content-Length', None):
                response['Content-Length'] = len(response.content)
        return response
