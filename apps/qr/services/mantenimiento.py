"""
Mantenimiento de los CÓDIGOS QR (lo que ejecuta `manage.py run_qr_maintenance`, normalmente programado a diario).

Flujo:
    1. Marcar como inactivos los QR que ya expiraron.
    2. Solo si la renovación está activada (configuración «Renovación automática» o la opción --renovar):
       renovar los QR vencidos de vehículos AUTORIZADOS cuyo propietario esté activo.

Un vehículo suspendido, no autorizado o con propietario inactivo NO se renueva: seguiría
sin poder ingresar y renovarlo solo ocultaría el motivo.
"""
from django.utils import timezone

from apps.vehiculos.models import Vehiculo

from ..models import CodigoQR, ConfiguracionQR


def expirar_vencidos(ahora=None):
    """Marca como inactivos los QR vencidos. Devuelve cuántos."""
    ahora = ahora or timezone.now()
    return CodigoQR.objects.filter(activo=True, fecha_expiracion__lte=ahora).update(activo=False)


def renovar_vencidos(ahora=None):
    """Renueva (token nuevo, imagen nueva y expiración nueva) los QR vencidos que pueden ingresar. Devuelve cuántos."""
    ahora = ahora or timezone.now()
    renovables = CodigoQR.objects.select_related('vehiculo').filter(
        fecha_expiracion__lte=ahora,
        vehiculo__estado=Vehiculo.AUTORIZADO,
        vehiculo__propietario__estado=True,
    )
    renovados = 0
    for codigo_qr in renovables:
        codigo_qr.renovar()
        renovados += 1
    return renovados


def ejecutar_mantenimiento(forzar_renovacion=False, ahora=None):
    """
    Expira los vencidos y renueva si corresponde. Devuelve (expirados, renovados, se_renovo).
    `forzar_renovacion` equivale a la opción --renovar del comando.
    """
    ahora = ahora or timezone.now()
    expirados = expirar_vencidos(ahora)
    renovar = forzar_renovacion or ConfiguracionQR.get_solo().renovacion_automatica
    renovados = renovar_vencidos(ahora) if renovar else 0
    return expirados, renovados, renovar
