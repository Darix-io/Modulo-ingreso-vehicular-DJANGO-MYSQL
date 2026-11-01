"""
Filtros y contadores de la lista de propietarios.

Los contadores de las pestañas respetan la búsqueda y el estado elegidos, pero no el
tipo (si no, cada pestaña mostraría 0 menos la que está seleccionada).
"""
from django.db.models import Count, Q

from .models import Propietario


def leer_filtros(params):
    """`params` es request.GET."""
    return {
        'q': params.get('q', '').strip(),
        'tipo': params.get('tipo', '').strip(),
        'estado': params.get('estado', '').strip().lower(),
    }


def _sin_tipo(filtros):
    queryset = Propietario.objects.all()
    if filtros['q']:
        queryset = queryset.filter(
            Q(nombre__icontains=filtros['q'])
            | Q(numero_identidad__icontains=filtros['q'])
            | Q(correo__icontains=filtros['q'])
        )
    if filtros['estado'] == 'activo':
        queryset = queryset.filter(estado=True)
    elif filtros['estado'] == 'inactivo':
        queryset = queryset.filter(estado=False)
    return queryset


def filtrar_propietarios(filtros):
    queryset = _sin_tipo(filtros)
    if filtros['tipo']:
        queryset = queryset.filter(tipo=filtros['tipo'])
    return queryset


def contadores_por_tipo(filtros):
    """Devuelve [{'valor': '', 'etiqueta': 'Todos', 'cantidad': N}, {'valor': 'Docente', ...}, ...]."""
    cantidades = dict(
        _sin_tipo(filtros).order_by().values_list('tipo').annotate(cantidad=Count('pk'))
    )
    pestanas = [{'valor': '', 'etiqueta': 'Todos', 'cantidad': sum(cantidades.values())}]
    for valor, etiqueta in Propietario.TIPO_CHOICES:
        pestanas.append({'valor': valor, 'etiqueta': etiqueta, 'cantidad': cantidades.get(valor, 0)})
    return pestanas
