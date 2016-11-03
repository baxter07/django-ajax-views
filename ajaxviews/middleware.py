from django.http import HttpResponseRedirect
from django.utils.encoding import force_text
from django.template.loader import get_template

from .conf import settings


class AjaxMiddleware:
    def process_response(self, request, response):
        if not request.is_ajax() and not isinstance(response, HttpResponseRedirect) and hasattr(response, 'content'):
            _content = force_text(response.content, encoding=response.charset)
            if '</body>' not in _content:
                return response

            json_cfg = {}
            if hasattr(response, 'context_data'):
                json_cfg = response.context_data.get('json_cfg', {})

            template = get_template('ajaxviews/__middleware.html')
            html = template.render({
                'json_cfg': json_cfg,
                'main_name': settings.REQUIRE_MAIN_NAME,
            })

            l_content, r_content = _content.rsplit('</body>', 1)
            _content = ''.join([l_content, html, '</body>', r_content])

            response.content = response.make_bytes(_content)
            if response.get('Content-Length', None):
                response['Content-Length'] = len(response.content)
        return response
