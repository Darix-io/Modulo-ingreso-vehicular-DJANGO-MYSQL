"""
Datos de apoyo para la pantalla de la garita (Validar acceso).

No existe el concepto de "turno" en el sistema, así que "los últimos accesos del turno"
son los movimientos de HOY (autorizados y denegados), del más reciente al más antiguo.
"""
from django.utils import timezone

from ..models import RegistroMovimiento

ACCESOS_RECIENTES = 5


def ultimos_accesos(limite=ACCESOS_RECIENTES, ahora=None):
    """Los últimos movimientos de hoy, con lo necesario para pintarlos sin más consultas."""
    ahora = timezone.localtime(ahora or timezone.now())
    inicio_del_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    return list(
        RegistroMovimiento.objects
        .filter(fecha__gte=inicio_del_dia)
        .select_related('vehiculo__propietario', 'usuario_validador')
        .order_by('-fecha', '-pk')[:limite]
    )
