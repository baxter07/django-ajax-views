from django.http import HttpResponseRedirect
from django.utils.encoding import force_text
from django.template.loader import get_template

from .conf import settings


class AjaxMiddleware:
    """
    This middleware inserts the **json config script** and the **require main script** inside
    the ``<body></body>`` tag on every non ajax request.

    .. code-block:: html
        :caption: base.html
        :name: JSON config script

        <script id="config" type="application/json">{{ json_cfg }}</script>

    .. code-block:: django
       :caption: base.html
       :name: require module

        {% load require %}
        {% require_module 'main' %}
    """
    def process_response(self, request, response):
        if not request.is_ajax() and not isinstance(response, HttpResponseRedirect) and hasattr(response, 'content'):
            content = force_text(response.content, encoding=response.charset)
            if '</body>' not in content:
                return response

            json_cfg = {}
            if hasattr(response, 'context_data'):
                json_cfg = response.context_data.get('json_cfg', {})

            template = get_template('ajaxviews/_middleware.html')
            html = template.render({
                'json_cfg': json_cfg,
                'main_name': settings.REQUIRE_MAIN_NAME,
            })

            l_content, r_content = content.rsplit('</body>', 1)
            content = ''.join([l_content, html, '</body>', r_content])

            response.content = response.make_bytes(content)
            if response.get('Content-Length', None):
                response['Content-Length'] = len(response.content)
        return response
