"""
Etiqueta de plantilla para conservar los filtros al cambiar de página.

Uso en una plantilla:
    {% load query_transform %}
    <a href="?{% query_transform page=2 %}">Siguiente</a>
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    query_params = context['request'].GET.copy()
    for clave, valor in kwargs.items():
        query_params[clave] = valor
    return query_params.urlencode()
