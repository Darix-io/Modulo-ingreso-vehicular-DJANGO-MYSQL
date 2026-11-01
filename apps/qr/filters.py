"""
Filtros y ordenamiento del historial de ingresos.

Lo usan la pantalla de historial, la de reportes y las exportaciones,
así que se escribe una sola vez aquí.
"""
from datetime import datetime

from django.db.models import Q

from .models import HistorialIngreso

ORDEN_POR_DEFECTO = '-fecha_ingreso'
ORDENES_PERMITIDOS = {
    'fecha_ingreso', '-fecha_ingreso',
    'vehiculo__placa', '-vehiculo__placa',
    'usuario_validador__username', '-usuario_validador__username',
}


def _parsear_fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _filtro_validador(texto):
    return (
        Q(usuario_validador__username__icontains=texto)
        | Q(usuario_validador__first_name__icontains=texto)
        | Q(usuario_validador__last_name__icontains=texto)
    )


def filtrar_historial(params, queryset=None):
    """`params` es request.GET. Devuelve el queryset filtrado."""
    if queryset is None:
        queryset = HistorialIngreso.objects.select_related('vehiculo', 'usuario_validador')

    q = params.get('q', '').strip()
    placa = params.get('placa', '').strip()
    validador = params.get('validador', '').strip()
    fecha_inicio = _parsear_fecha(params.get('fecha_inicio', '').strip())
    fecha_final = _parsear_fecha(params.get('fecha_final', '').strip())

    if q:
        queryset = queryset.filter(
            Q(vehiculo__placa__icontains=q)
            | Q(vehiculo__marca__icontains=q)
            | Q(vehiculo__modelo__icontains=q)
            | _filtro_validador(q)
        )
    if placa:
        queryset = queryset.filter(vehiculo__placa__icontains=placa)
    if validador:
        queryset = queryset.filter(_filtro_validador(validador))
    if fecha_inicio:
        queryset = queryset.filter(fecha_ingreso__date__gte=fecha_inicio)
    if fecha_final:
        queryset = queryset.filter(fecha_ingreso__date__lte=fecha_final)

    return queryset


def orden_seguro(params):
    """Solo acepta columnas conocidas (evita ordenar por cualquier campo)."""
    orden = params.get('orden', ORDEN_POR_DEFECTO)
    return orden if orden in ORDENES_PERMITIDOS else ORDEN_POR_DEFECTO


def orden_alterno(orden_actual, campo):
    """Para los encabezados de tabla: si ya está ascendente, el enlace ordena descendente."""
    return f'-{campo}' if orden_actual == campo else campo
