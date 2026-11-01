"""
Números de la pantalla MOVIMIENTOS: lo que pasó hoy en la garita.

Cuenta intentos (autorizados y denegados). "Ingresos" y "salidas" son solo los
autorizados: un intento denegado no es un tránsito real.
"""
from django.db.models import Count, Q
from django.utils import timezone

from ..models import RegistroMovimiento


def _porcentaje(parte, total):
    """Porcentaje con un decimal; None si no hay intentos (no se muestra un 0 % engañoso)."""
    return round(parte * 100 / total, 1) if total else None


def contadores_hoy(ahora=None):
    """Total de hoy, autorizados, denegados, ingresos y salidas (autorizados) y los porcentajes."""
    ahora = timezone.localtime(ahora or timezone.now())
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    autorizado = Q(estado=RegistroMovimiento.AUTORIZADO)
    cuentas = RegistroMovimiento.objects.filter(fecha__gte=inicio).aggregate(
        total=Count('pk'),
        autorizados=Count('pk', filter=autorizado),
        denegados=Count('pk', filter=Q(estado=RegistroMovimiento.DENEGADO)),
        ingresos=Count('pk', filter=autorizado & Q(tipo=RegistroMovimiento.INGRESO)),
        salidas=Count('pk', filter=autorizado & Q(tipo=RegistroMovimiento.SALIDA)),
    )
    cuentas['pct_autorizados'] = _porcentaje(cuentas['autorizados'], cuentas['total'])
    cuentas['pct_denegados'] = _porcentaje(cuentas['denegados'], cuentas['total'])
    return cuentas
