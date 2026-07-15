from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    request = context['request']
    query_params = request.GET.copy()
    for k, v in kwargs.items():
        query_params[k] = v
    return query_params.urlencode()
