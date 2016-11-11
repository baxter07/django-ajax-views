from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def container_size(context):
    if not context.get('page_size', None):
        return 'container'
    class_str = 'container-' + context['page_size']
    if context.get('sidebar_offset', None):
        class_str += '-sidebar-offset-' + context['sidebar_offset']
    return class_str


@register.simple_tag(takes_context=True)
def sidebar_offset(context):
    if context.get('sidebar_offset', None):
        return 'sidebar-offset-' + context['sidebar_offset']
    return ''
