"""Reglas de negocio de vehículos que no caben en el modelo."""
from apps.qr.models import CodigoQR, HistorialIngreso, RegistroMovimiento


def resumen_eliminacion(vehiculo):
    """
    Qué se borra EN CASCADA si se elimina el vehículo (lo definen los ForeignKey).
    Se muestra en la pantalla de confirmación para que la decisión sea informada.
    """
    return {
        'total_qr': CodigoQR.objects.filter(vehiculo=vehiculo).count(),
        'total_ingresos': HistorialIngreso.objects.filter(vehiculo=vehiculo).count(),
        'total_movimientos': RegistroMovimiento.objects.filter(vehiculo=vehiculo).count(),
    }
