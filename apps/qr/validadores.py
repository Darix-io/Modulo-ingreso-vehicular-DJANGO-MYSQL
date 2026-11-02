"""Reglas de validación de la configuración de los QR (se prueban solas, sin formulario)."""
from django.core.exceptions import ValidationError

DIAS_MINIMO = 1
DIAS_MAXIMO = 365


def validar_dias_vigencia(dias):
    """La vigencia de un QR va de 1 a 365 días. Devuelve el número entero o lanza ValidationError."""
    if dias is None:
        raise ValidationError('Escribe cuántos días durará la vigencia.')
    if dias < DIAS_MINIMO or dias > DIAS_MAXIMO:
        raise ValidationError(f'La vigencia debe estar entre {DIAS_MINIMO} y {DIAS_MAXIMO} días.')
    return dias
