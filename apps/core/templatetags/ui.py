"""
Filtros de plantilla para la interfaz.

Uso en una plantilla:
    {% load ui %}
    {{ usuario.get_full_name|iniciales }}
"""
from django import template

register = template.Library()


@register.filter
def iniciales(nombre):
    """'Juan Carlos Pérez' -> 'JC'. Sin nombre devuelve '?'."""
    partes = str(nombre or '').split()
    if not partes:
        return '?'
    return ''.join(p[0] for p in partes[:2]).upper()
