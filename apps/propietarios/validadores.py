"""
Validaciones del propietario (separadas del formulario para poder probarlas solas).

- Cédula: exactamente 10 dígitos. Los VISITANTES pueden usar otro documento
  (pasaporte, etc.) de 6 a 20 caracteres.
- Celular: 10 dígitos que empiecen con 09.
"""
import re

from django.core.exceptions import ValidationError

TIPO_VISITANTE = 'Visitante'


def validar_documento(numero, tipo):
    """Devuelve el documento limpio o lanza ValidationError."""
    numero = (numero or '').strip()
    if tipo == TIPO_VISITANTE:
        if not 6 <= len(numero) <= 20:
            raise ValidationError('El documento del visitante debe tener entre 6 y 20 caracteres.')
        if not re.fullmatch(r'[A-Za-z0-9]+', numero):
            raise ValidationError('El documento solo puede tener letras y números, sin espacios.')
        return numero.upper()
    if not re.fullmatch(r'[0-9]{10}', numero):
        raise ValidationError('La cédula debe tener exactamente 10 dígitos numéricos.')
    return numero


def validar_celular(celular):
    """Devuelve el celular limpio o lanza ValidationError."""
    celular = (celular or '').strip()
    if not re.fullmatch(r'09[0-9]{8}', celular):
        raise ValidationError('El celular debe tener 10 dígitos y empezar con 09.')
    return celular
