"""
Filtros y contadores de la lista de vehículos.

Las tarjetas de contadores respetan la búsqueda, pero no el estado elegido
(si no, al filtrar por un estado las otras tarjetas mostrarían 0).
"""
from django.db.models import Count, Q

from .models import Vehiculo

# Valor que llega en la URL (?estado=...) -> valor guardado en la BD
ESTADOS_URL = {
    'autorizado': Vehiculo.AUTORIZADO,
    'no_autorizado': Vehiculo.NO_AUTORIZADO,
    'suspendido': Vehiculo.SUSPENDIDO,
}

ETIQUETAS_ESTADO = {
    'autorizado': 'Autorizados',
    'no_autorizado': 'No autorizados',
    'suspendido': 'Suspendidos',
}


def leer_filtros(params):
    """`params` es request.GET."""
    return {
        'q': params.get('q', '').strip(),
        'estado': params.get('estado', '').strip().lower(),
    }


def _sin_estado(filtros):
    queryset = Vehiculo.objects.select_related('propietario', 'codigo_qr')
    if filtros['q']:
        queryset = queryset.filter(
            Q(placa__icontains=filtros['q'])
            | Q(marca__icontains=filtros['q'])
            | Q(modelo__icontains=filtros['q'])
            | Q(propietario__nombre__icontains=filtros['q'])
            | Q(propietario__numero_identidad__icontains=filtros['q'])
        )
    return queryset


def filtrar_vehiculos(filtros):
    queryset = _sin_estado(filtros)
    if filtros['estado'] in ESTADOS_URL:
        queryset = queryset.filter(estado=ESTADOS_URL[filtros['estado']])
    return queryset


def contadores_por_estado(filtros):
    """Devuelve [{'clave': 'autorizado', 'etiqueta': 'Autorizados', 'cantidad': N}, ...]."""
    cantidades = dict(
        _sin_estado(filtros).order_by().values_list('estado').annotate(cantidad=Count('pk'))
    )
    return [
        {'clave': clave, 'etiqueta': ETIQUETAS_ESTADO[clave], 'cantidad': cantidades.get(valor, 0)}
        for clave, valor in ESTADOS_URL.items()
    ]
