"""
Filtros y ordenamiento de MOVIMIENTOS y del HISTORIAL de ingresos.

Los usan las pantallas de movimientos, historial y reportes y las exportaciones,
así que se escriben una sola vez aquí. Todos reciben `request.GET` (o un dict).
"""
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import HistorialIngreso, RegistroMovimiento

ORDEN_POR_DEFECTO = '-fecha_ingreso'
ORDENES_PERMITIDOS = {
    'fecha_ingreso', '-fecha_ingreso',
    'vehiculo__placa', '-vehiculo__placa',
    'usuario_validador__username', '-usuario_validador__username',
}

# Valor de la URL (?tipo=, ?estado=) -> constante del modelo
TIPOS_URL = {'ingreso': RegistroMovimiento.INGRESO, 'salida': RegistroMovimiento.SALIDA}
ESTADOS_URL = {'autorizado': RegistroMovimiento.AUTORIZADO, 'denegado': RegistroMovimiento.DENEGADO}


def parsear_fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def parsear_entero(texto):
    try:
        return int(texto)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ movimientos
def leer_filtros_movimientos(params):
    """Normaliza lo que llega por URL: valores desconocidos se ignoran (nunca dan error)."""
    tipo = params.get('tipo', '').strip().lower()
    estado = params.get('estado', '').strip().lower()
    return {
        'placa': params.get('placa', '').strip(),
        'tipo': tipo if tipo in TIPOS_URL else '',
        'estado': estado if estado in ESTADOS_URL else '',
    }


def filtrar_movimientos(filtros, queryset=None):
    """`filtros` sale de `leer_filtros_movimientos`."""
    if queryset is None:
        queryset = RegistroMovimiento.objects.select_related(
            'vehiculo__propietario', 'usuario_validador')
    if filtros['placa']:
        queryset = queryset.filter(vehiculo__placa__icontains=filtros['placa'])
    if filtros['tipo']:
        queryset = queryset.filter(tipo=TIPOS_URL[filtros['tipo']])
    if filtros['estado']:
        queryset = queryset.filter(estado=ESTADOS_URL[filtros['estado']])
    return queryset


# ------------------------------------------------------------------ historial
def _filtro_validador(texto):
    return (
        Q(usuario_validador__username__icontains=texto)
        | Q(usuario_validador__first_name__icontains=texto)
        | Q(usuario_validador__last_name__icontains=texto)
    )


def filtrar_historial(params, queryset=None):
    """
    `params` es request.GET. Devuelve el queryset filtrado.
    q = texto libre (placa, marca, modelo, propietario, cédula o guardia);
    placa = parte de la placa; validador = id del guardia; fecha_inicio / fecha_final = AAAA-MM-DD.
    """
    if queryset is None:
        queryset = HistorialIngreso.objects.select_related('vehiculo__propietario', 'usuario_validador')

    q = params.get('q', '').strip()
    placa = params.get('placa', '').strip()
    validador = parsear_entero(params.get('validador', '').strip())
    fecha_inicio = parsear_fecha(params.get('fecha_inicio', '').strip())
    fecha_final = parsear_fecha(params.get('fecha_final', '').strip())

    if q:
        queryset = queryset.filter(
            Q(vehiculo__placa__icontains=q)
            | Q(vehiculo__marca__icontains=q)
            | Q(vehiculo__modelo__icontains=q)
            | Q(vehiculo__propietario__nombre__icontains=q)
            | Q(vehiculo__propietario__numero_identidad__icontains=q)
            | _filtro_validador(q)
        )
    if placa:
        queryset = queryset.filter(vehiculo__placa__icontains=placa)
    if validador is not None:
        queryset = queryset.filter(usuario_validador_id=validador)
    if fecha_inicio:
        queryset = queryset.filter(fecha_ingreso__date__gte=fecha_inicio)
    if fecha_final:
        queryset = queryset.filter(fecha_ingreso__date__lte=fecha_final)

    return queryset


def rango_invalido(params):
    """True si la fecha inicial es posterior a la final (el resultado sería siempre vacío)."""
    inicio = parsear_fecha(params.get('fecha_inicio', '').strip())
    final = parsear_fecha(params.get('fecha_final', '').strip())
    return bool(inicio and final and inicio > final)


def rangos_rapidos(hoy=None):
    """Atajos de fechas para el formulario: (texto, fecha_inicio, fecha_final) en formato AAAA-MM-DD."""
    hoy = hoy or timezone.localdate()
    return [
        ('Hoy', hoy.isoformat(), hoy.isoformat()),
        ('Últimos 7 días', (hoy - timedelta(days=6)).isoformat(), hoy.isoformat()),
        ('Este mes', hoy.replace(day=1).isoformat(), hoy.isoformat()),
    ]


def orden_seguro(params):
    """Solo acepta columnas conocidas (evita ordenar por cualquier campo)."""
    orden = params.get('orden', ORDEN_POR_DEFECTO)
    return orden if orden in ORDENES_PERMITIDOS else ORDEN_POR_DEFECTO


def orden_alterno(orden_actual, campo):
    """Para los encabezados de tabla: si ya está ascendente, el enlace ordena descendente."""
    return f'-{campo}' if orden_actual == campo else campo
