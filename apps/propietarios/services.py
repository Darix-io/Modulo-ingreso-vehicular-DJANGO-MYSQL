"""Reglas de negocio de propietarios que no caben en el modelo."""
from apps.qr.models import CodigoQR, HistorialIngreso, RegistroMovimiento


def resumen_eliminacion(propietario):
    """
    Qué se borra EN CASCADA si se elimina al propietario (lo definen los ForeignKey).
    Se muestra en la pantalla de confirmación para que la decisión sea informada.
    """
    vehiculos = list(propietario.vehiculos.all())
    return {
        'vehiculos': vehiculos,
        'total_vehiculos': len(vehiculos),
        'total_qr': CodigoQR.objects.filter(vehiculo__propietario=propietario).count(),
        'total_movimientos': RegistroMovimiento.objects.filter(vehiculo__propietario=propietario).count(),
        'total_ingresos': HistorialIngreso.objects.filter(vehiculo__propietario=propietario).count(),
    }
