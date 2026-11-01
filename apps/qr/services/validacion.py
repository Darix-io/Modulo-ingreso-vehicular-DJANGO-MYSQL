"""
Reglas de CONTROL DE ACCESO (validar un QR en la garita).

Flujo:
    1. Limpiar el texto escaneado y obtener el token (UUID).
    2. Buscar el código QR.
    3. Decidir si es INGRESO o SALIDA (alterna según el último movimiento autorizado).
    4. Revisar todas las reglas. Si alguna falla -> DENEGADO.
    5. Guardar el movimiento (y el historial si es un ingreso autorizado).

Correcciones respecto a la versión anterior:
    - Un vehículo SUSPENDIDO o NO AUTORIZADO ya no puede entrar.
    - Un vehículo cuyo propietario está INACTIVO ya no puede entrar.
    - Un texto que no es un UUID ya no rompe la página (antes daba error 500).
    - Todo se guarda dentro de una transacción.
"""
import uuid
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

from django.db import transaction

from apps.vehiculos.models import Vehiculo

from ..models import CodigoQR, ConfiguracionQR, HistorialIngreso, RegistroMovimiento


@dataclass
class ResultadoValidacion:
    """Lo que la vista necesita para mostrar la pantalla de éxito o error."""
    autorizado: bool
    mensaje: str
    vehiculo: Optional[Vehiculo] = None
    tipo: Optional[str] = None
    movimiento: Optional[RegistroMovimiento] = None

    @property
    def status(self):
        # Las plantillas usan 'success' / 'danger' (clases de Bootstrap)
        return 'success' if self.autorizado else 'danger'


def extraer_token(texto):
    """
    Acepta el token solo, o la URL completa del QR (…/qr/validar/?token=XXXX).
    Devuelve el UUID como texto, o None si no es válido.
    """
    if not texto:
        return None
    texto = str(texto).strip().lstrip('+')

    if 'token=' in texto:
        valores = parse_qs(urlparse(texto).query).get('token')
        if valores:
            texto = valores[0].strip().lstrip('+')

    try:
        return str(uuid.UUID(texto))
    except (ValueError, AttributeError):
        return None


def siguiente_tipo_movimiento(codigo_qr):
    """Si lo último autorizado fue un INGRESO, ahora toca SALIDA (y viceversa)."""
    ultimo = (
        codigo_qr.movimientos
        .filter(estado=RegistroMovimiento.AUTORIZADO)
        .order_by('-fecha')
        .first()
    )
    if ultimo and ultimo.tipo == RegistroMovimiento.INGRESO:
        return RegistroMovimiento.SALIDA
    return RegistroMovimiento.INGRESO


def motivo_de_rechazo(codigo_qr, configuracion):
    """Devuelve el texto del motivo si NO puede pasar, o None si todo está bien."""
    vehiculo = codigo_qr.vehiculo

    if not configuracion.activar_qr:
        return 'Validación de QR deshabilitada'
    if not codigo_qr.activo:
        return 'Código desactivado'
    if codigo_qr.is_expired:
        return 'Código expirado'
    if vehiculo.estado != Vehiculo.AUTORIZADO:
        return f'Vehículo {vehiculo.get_estado_display().lower()}'
    if not vehiculo.propietario.estado:
        return 'Propietario inactivo'
    return None


def validar_acceso(texto_escaneado, usuario):
    """Punto de entrada que usa la vista. Siempre devuelve un ResultadoValidacion."""
    token = extraer_token(texto_escaneado)
    if token is None:
        return ResultadoValidacion(autorizado=False, mensaje='Código no válido')

    try:
        codigo_qr = (
            CodigoQR.objects
            .select_related('vehiculo__propietario')
            .get(contenido=token)
        )
    except CodigoQR.DoesNotExist:
        return ResultadoValidacion(autorizado=False, mensaje='Código no válido')

    configuracion = ConfiguracionQR.get_solo()
    tipo = siguiente_tipo_movimiento(codigo_qr)
    validador = usuario if usuario.is_authenticated else None
    motivo = motivo_de_rechazo(codigo_qr, configuracion)

    with transaction.atomic():
        if codigo_qr.is_expired and codigo_qr.activo:
            codigo_qr.activo = False
            codigo_qr.save(update_fields=['activo'])

        if motivo:
            RegistroMovimiento.objects.create(
                codigo_qr=codigo_qr,
                vehiculo=codigo_qr.vehiculo,
                tipo=tipo,
                estado=RegistroMovimiento.DENEGADO,
                usuario_validador=validador,
                detalle=motivo,
            )
            return ResultadoValidacion(
                autorizado=False, mensaje=motivo, vehiculo=codigo_qr.vehiculo, tipo=tipo,
            )

        es_ingreso = tipo == RegistroMovimiento.INGRESO
        movimiento = RegistroMovimiento.objects.create(
            codigo_qr=codigo_qr,
            vehiculo=codigo_qr.vehiculo,
            tipo=tipo,
            estado=RegistroMovimiento.AUTORIZADO,
            usuario_validador=validador,
            detalle='Acceso autorizado' if es_ingreso else 'Salida autorizada',
        )
        if es_ingreso:
            HistorialIngreso.objects.create(vehiculo=codigo_qr.vehiculo, usuario_validador=validador)

    return ResultadoValidacion(
        autorizado=True,
        mensaje='Ingreso Autorizado' if es_ingreso else 'Salida Autorizada',
        vehiculo=codigo_qr.vehiculo,
        tipo=tipo,
        movimiento=movimiento,
    )
