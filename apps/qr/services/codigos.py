"""
Reglas de los CÓDIGOS QR para las pantallas de lista, detalle y credencial.

Una sola definición de "estado" para todo el sistema (lista, panel y detalle):
    - VIGENTE:      activo y todavía no expira.
    - POR VENCER:   vigente y vence en 3 días o menos.
    - EXPIRADO:     ya pasó su fecha de expiración.
    - INACTIVO:     fue desactivado (activo = False) sin haber expirado.
    "Expirados o inactivos" = todo lo que no es vigente.
"""
import math
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from ..models import CodigoQR, HistorialIngreso

DIAS_POR_VENCER = 3     # un QR "por vencer" vence en 3 días o menos

# Valor que llega en la URL (?estado=...)
ESTADOS_URL = ('vigentes', 'por_vencer', 'no_vigentes')


# --------------------------------------------------------------------- consultas
def qr_vigentes(queryset, ahora):
    return queryset.filter(activo=True, fecha_expiracion__gt=ahora)


def qr_por_vencer(queryset, ahora):
    return qr_vigentes(queryset, ahora).filter(
        fecha_expiracion__lte=ahora + timedelta(days=DIAS_POR_VENCER))


def qr_no_vigentes(queryset, ahora):
    """Expirados o inactivos."""
    return queryset.filter(Q(activo=False) | Q(fecha_expiracion__lte=ahora))


def buscar_codigos(queryset, texto):
    """Busca por placa, nombre del propietario o su cédula."""
    texto = (texto or '').strip()
    if not texto:
        return queryset
    return queryset.filter(
        Q(vehiculo__placa__icontains=texto)
        | Q(vehiculo__propietario__nombre__icontains=texto)
        | Q(vehiculo__propietario__numero_identidad__icontains=texto)
    )


def filtrar_por_estado(queryset, estado, ahora):
    if estado == 'vigentes':
        return qr_vigentes(queryset, ahora)
    if estado == 'por_vencer':
        return qr_por_vencer(queryset, ahora)
    if estado == 'no_vigentes':
        return qr_no_vigentes(queryset, ahora)
    return queryset


def contadores_qr(queryset, ahora):
    """Cantidades para las tarjetas de la lista (sobre el queryset ya buscado)."""
    return {
        'vigentes': qr_vigentes(queryset, ahora).count(),
        'por_vencer': qr_por_vencer(queryset, ahora).count(),
        'no_vigentes': qr_no_vigentes(queryset, ahora).count(),
        'total': queryset.count(),
    }


# --------------------------------------------------------------------- vigencia
def vigencia_qr(codigo, ahora=None):
    """
    Estado y tiempo restante de UN código, listo para mostrar.
    Devuelve: clave ('vigente'|'por_vencer'|'expirado'|'inactivo'), texto, tono (para el badge),
    dias_restantes, dias_vencido, porcentaje (0-100 de la vida del QR ya transcurrida).
    """
    ahora = ahora or timezone.now()
    restante = codigo.fecha_expiracion - ahora
    expirado = restante.total_seconds() <= 0

    if expirado:
        clave, texto, tono = 'expirado', 'Expirado', 'rojo'
    elif not codigo.activo:
        clave, texto, tono = 'inactivo', 'Inactivo', 'gris'
    elif restante <= timedelta(days=DIAS_POR_VENCER):
        clave, texto, tono = 'por_vencer', 'Por vencer', 'ambar'
    else:
        clave, texto, tono = 'vigente', 'Vigente', 'verde'

    vida = (codigo.fecha_expiracion - codigo.fecha_creacion).total_seconds()
    transcurrido = (ahora - codigo.fecha_creacion).total_seconds()
    porcentaje = 100 if expirado else (int(min(100, max(0, transcurrido * 100 / vida))) if vida > 0 else 0)

    return {
        'clave': clave,
        'texto': texto,
        'tono': tono,
        'es_vigente': clave in ('vigente', 'por_vencer'),
        'dias_restantes': 0 if expirado else math.ceil(restante.total_seconds() / 86400),
        'dias_vencido': (ahora - codigo.fecha_expiracion).days if expirado else 0,
        'porcentaje': porcentaje,
    }


def anotar_vigencia(codigos, ahora=None):
    """Agrega `.vigencia` a cada código de la lista (así la plantilla no calcula nada)."""
    ahora = ahora or timezone.now()
    for codigo in codigos:
        codigo.vigencia = vigencia_qr(codigo, ahora)
    return codigos


# --------------------------------------------------------------------- resumen de accesos
def resumen_accesos(vehiculo, ahora=None):
    """
    Para el Detalle QR: último ingreso AUTORIZADO del vehículo (fecha, hora y guardia)
    y cuántos ingresos lleva en el mes en curso.
    """
    ahora = ahora or timezone.now()
    inicio_mes = timezone.localtime(ahora).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    ingresos = HistorialIngreso.objects.filter(vehiculo=vehiculo)
    ultimo = ingresos.select_related('usuario_validador').order_by('-fecha_ingreso').first()
    guardia = None
    if ultimo and ultimo.usuario_validador:
        guardia = ultimo.usuario_validador.get_full_name() or ultimo.usuario_validador.username

    return {
        'ultimo_ingreso': ultimo,
        'guardia': guardia,
        'total_mes': ingresos.filter(fecha_ingreso__gte=inicio_mes).count(),
        'total_historico': ingresos.count(),
        'mes': inicio_mes,
    }
