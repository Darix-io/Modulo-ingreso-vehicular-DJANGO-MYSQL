"""
Cálculos del PANEL DE CONTROL (dashboard).

Antes todo esto estaba dentro de DashboardView y hacía 14 consultas solo
para el gráfico por horas. Ahora el gráfico se arma con UNA consulta.
Las claves del diccionario son las mismas que ya usa dashboard.html.
"""
from collections import Counter
from datetime import datetime, time, timedelta

from django.utils import timezone

from apps.propietarios.models import Propietario
from apps.vehiculos.models import Vehiculo

from ..models import CodigoQR, ConfiguracionQR, HistorialIngreso, RegistroMovimiento

HORAS_GRAFICO = range(6, 19, 2)   # 06:00, 08:00, ... 18:00 (bloques de 2 horas)
DIAS_POR_VENCER = 3               # un QR "por vencer" vence en 3 días o menos


def saludo(ahora=None):
    """'Buenos días' / 'Buenas tardes' / 'Buenas noches' según la hora local."""
    hora = timezone.localtime(ahora).hour if ahora else timezone.localtime().hour
    if hora < 12:
        return 'Buenos días'
    if hora < 19:
        return 'Buenas tardes'
    return 'Buenas noches'


def _variacion_pct(actual, anterior):
    """Cambio porcentual respecto al periodo anterior. None si no hay base para comparar."""
    if not anterior:
        return None
    return round((actual - anterior) * 100 / anterior, 1)


def _porcentaje(parte, total):
    """Porcentaje con un decimal. None si no hay intentos (para no mostrar 0 % engañoso)."""
    if not total:
        return None
    return round(parte * 100 / total, 1)


def _causa_frecuente(denegados_hoy):
    """El motivo de denegación más repetido hoy: (texto, cantidad) o None."""
    motivos = Counter(denegados_hoy.values_list('detalle', flat=True))
    if not motivos:
        return None
    return motivos.most_common(1)[0]


def _inicio_del_dia(fecha):
    return timezone.make_aware(datetime.combine(fecha, time.min))


def _contar_ingresos(desde, hasta=None):
    filtros = {'fecha_ingreso__gte': desde}
    if hasta is not None:
        filtros['fecha_ingreso__lt'] = hasta
    return HistorialIngreso.objects.filter(**filtros).count()


def _comparativos_ingresos(hoy):
    inicio_hoy = _inicio_del_dia(hoy)
    inicio_manana = inicio_hoy + timedelta(days=1)
    inicio_ayer = inicio_hoy - timedelta(days=1)

    inicio_semana = inicio_hoy - timedelta(days=hoy.weekday())
    inicio_semana_pasada = inicio_semana - timedelta(days=7)

    inicio_mes = _inicio_del_dia(hoy.replace(day=1))
    inicio_mes_pasado = _inicio_del_dia((hoy.replace(day=1) - timedelta(days=1)).replace(day=1))

    datos = {
        'ingresos_hoy': _contar_ingresos(inicio_hoy, inicio_manana),
        'ingresos_ayer': _contar_ingresos(inicio_ayer, inicio_hoy),
        'ingresos_semana_actual': _contar_ingresos(inicio_semana),
        'ingresos_semana_pasada': _contar_ingresos(inicio_semana_pasada, inicio_semana),
        'ingresos_mes_actual': _contar_ingresos(inicio_mes),
        'ingresos_mes_pasado': _contar_ingresos(inicio_mes_pasado, inicio_mes),
    }
    datos['diferencia_ingresos'] = datos['ingresos_hoy'] - datos['ingresos_ayer']
    datos['diferencia_semana'] = datos['ingresos_semana_actual'] - datos['ingresos_semana_pasada']
    datos['diferencia_mes'] = datos['ingresos_mes_actual'] - datos['ingresos_mes_pasado']
    return datos


def _grafico_accesos_por_hora(movimientos_hoy):
    """Agrupa autorizados/denegados en bloques de 2 horas con una sola consulta."""
    autorizados = {hora: 0 for hora in HORAS_GRAFICO}
    denegados = {hora: 0 for hora in HORAS_GRAFICO}

    for fecha, estado in movimientos_hoy.values_list('fecha', 'estado'):
        hora_local = timezone.localtime(fecha).hour
        bloque = hora_local - (hora_local % 2)
        if bloque not in autorizados:
            continue
        if estado == RegistroMovimiento.AUTORIZADO:
            autorizados[bloque] += 1
        else:
            denegados[bloque] += 1

    return {
        'access_chart_labels': [f'{hora:02d}:00' for hora in HORAS_GRAFICO],
        'access_chart_autorizados': list(autorizados.values()),
        'access_chart_denegados': list(denegados.values()),
    }


def resumen_dashboard():
    ahora = timezone.now()
    hoy = timezone.localdate()
    inicio_hoy = _inicio_del_dia(hoy)
    configuracion = ConfiguracionQR.get_solo()

    movimientos_hoy = RegistroMovimiento.objects.filter(
        fecha__gte=inicio_hoy, fecha__lt=inicio_hoy + timedelta(days=1),
    )
    autorizados = movimientos_hoy.filter(estado=RegistroMovimiento.AUTORIZADO)
    denegados = movimientos_hoy.filter(estado=RegistroMovimiento.DENEGADO)
    autorizados_hoy = autorizados.count()
    denegados_hoy = denegados.count()
    intentos_hoy = autorizados_hoy + denegados_hoy
    porcentaje_exito = _porcentaje(autorizados_hoy, intentos_hoy)

    contexto = {
        'fecha_hoy': hoy.isoformat(),
        'total_propietarios': Propietario.objects.count(),
        'total_vehiculos': Vehiculo.objects.count(),
        'total_accesos': HistorialIngreso.objects.count(),
        'qr_expiration_days': configuracion.expiration_days,
        'qr_activada': configuracion.activar_qr,
        'qr_reutilizable': configuracion.permitir_reutilizacion,
        'autorizados_hoy': autorizados_hoy,
        'denegados_hoy': denegados_hoy,
        'intentos_hoy': intentos_hoy,
        'porcentaje_exito': porcentaje_exito,
        'porcentaje_exito_ancho': int(porcentaje_exito or 0),   # entero: se usa en un style="width"
        'porcentaje_rechazo': _porcentaje(denegados_hoy, intentos_hoy),
        'causa_frecuente': _causa_frecuente(denegados),
        'qr_activos': CodigoQR.objects.filter(activo=True, fecha_expiracion__gt=ahora).count(),
        'qr_proximos_vencer': CodigoQR.objects.filter(
            activo=True,
            fecha_expiracion__gt=ahora,
            fecha_expiracion__lte=ahora + timedelta(days=DIAS_POR_VENCER),
        ).count(),
        'recent_movements': movimientos_hoy
            .select_related('vehiculo__propietario', 'usuario_validador')
            .order_by('-fecha')[:5],
    }
    contexto.update(_comparativos_ingresos(hoy))
    contexto['variacion_semana_pct'] = _variacion_pct(
        contexto['ingresos_semana_actual'], contexto['ingresos_semana_pasada'])
    contexto['variacion_mes_pct'] = _variacion_pct(
        contexto['ingresos_mes_actual'], contexto['ingresos_mes_pasado'])
    contexto.update(_grafico_accesos_por_hora(movimientos_hoy))
    return contexto
