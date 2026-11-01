"""
Reglas de CONTROL DE ACCESO (validar un QR, o la placa a mano, en la garita).

Flujo (igual para el QR y para la placa; solo cambia cómo se encuentra el código):
    1. Encontrar el código QR: por el token escaneado o por la placa escrita.
    2. Decidir si es INGRESO o SALIDA (alterna según el último movimiento autorizado).
    3. Revisar todas las reglas (`motivo_de_rechazo`). Si alguna falla -> DENEGADO.
    4. Guardar el movimiento (y el historial si es un ingreso autorizado).

Correcciones respecto a la versión anterior:
    - Un vehículo SUSPENDIDO o NO AUTORIZADO ya no puede entrar.
    - Un vehículo cuyo propietario está INACTIVO ya no puede entrar.
    - Un texto que no es un UUID ya no rompe la página (antes daba error 500).
    - Todo se guarda dentro de una transacción.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs, urlparse

from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Replace
from django.utils import timezone

from apps.vehiculos.models import Vehiculo

from ..models import CodigoQR, ConfiguracionQR, HistorialIngreso, RegistroMovimiento

CODIGO_NO_VALIDO = 'Código no válido'
PLACA_NO_REGISTRADA = 'Placa no registrada'
DETALLE_MANUAL = 'Validación manual por placa'

# Texto del motivo según el estado del vehículo (no se usa get_estado_display: dice "Acceso suspendido")
MOTIVOS_POR_ESTADO = {
    Vehiculo.SUSPENDIDO: 'Vehículo suspendido',
    Vehiculo.NO_AUTORIZADO: 'Vehículo no autorizado',
}


@dataclass
class ResultadoValidacion:
    """Lo que la vista necesita para mostrar la pantalla de éxito o de rechazo."""
    autorizado: bool
    mensaje: str
    vehiculo: Optional[Vehiculo] = None
    tipo: Optional[str] = None
    movimiento: Optional[RegistroMovimiento] = None
    codigo_qr: Optional[CodigoQR] = None
    manual: bool = False
    fecha: datetime = field(default_factory=timezone.now)

    @property
    def es_ingreso(self):
        return self.tipo == RegistroMovimiento.INGRESO


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


def normalizar_placa(texto):
    """'gsa 3841' -> 'GSA3841' (mayúsculas, sin espacios ni guion), para comparar sin importar cómo se escribió."""
    return ''.join(str(texto or '').split()).replace('-', '').upper()


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
        return MOTIVOS_POR_ESTADO.get(vehiculo.estado, 'Vehículo no autorizado')
    if not vehiculo.propietario.estado:
        return 'Propietario inactivo'
    return None


def _registrar(codigo_qr, usuario, manual=False):
    """Aplica las reglas a un código ya encontrado y guarda el movimiento (QR y placa comparten esto)."""
    configuracion = ConfiguracionQR.get_solo()
    tipo = siguiente_tipo_movimiento(codigo_qr)
    validador = usuario if usuario.is_authenticated else None
    motivo = motivo_de_rechazo(codigo_qr, configuracion)
    vehiculo = codigo_qr.vehiculo

    with transaction.atomic():
        if codigo_qr.is_expired and codigo_qr.activo:
            codigo_qr.activo = False
            codigo_qr.save(update_fields=['activo'])

        if motivo:
            # En los denegados el detalle es SIEMPRE el motivo real (así Movimientos y el panel los agrupan)
            movimiento = RegistroMovimiento.objects.create(
                codigo_qr=codigo_qr, vehiculo=vehiculo, tipo=tipo,
                estado=RegistroMovimiento.DENEGADO, usuario_validador=validador, detalle=motivo,
            )
            return ResultadoValidacion(
                autorizado=False, mensaje=motivo, vehiculo=vehiculo, tipo=tipo,
                movimiento=movimiento, codigo_qr=codigo_qr, manual=manual, fecha=movimiento.fecha,
            )

        es_ingreso = tipo == RegistroMovimiento.INGRESO
        if manual:
            detalle = DETALLE_MANUAL
        else:
            detalle = 'Acceso autorizado' if es_ingreso else 'Salida autorizada'
        movimiento = RegistroMovimiento.objects.create(
            codigo_qr=codigo_qr, vehiculo=vehiculo, tipo=tipo,
            estado=RegistroMovimiento.AUTORIZADO, usuario_validador=validador, detalle=detalle,
        )
        if es_ingreso:
            HistorialIngreso.objects.create(vehiculo=vehiculo, usuario_validador=validador)

    return ResultadoValidacion(
        autorizado=True,
        mensaje='Ingreso autorizado' if es_ingreso else 'Salida autorizada',
        vehiculo=vehiculo, tipo=tipo, movimiento=movimiento, codigo_qr=codigo_qr,
        manual=manual, fecha=movimiento.fecha,
    )


def validar_acceso(texto_escaneado, usuario):
    """Valida un QR escaneado. Siempre devuelve un ResultadoValidacion."""
    token = extraer_token(texto_escaneado)
    if token is None:
        return ResultadoValidacion(autorizado=False, mensaje=CODIGO_NO_VALIDO)

    try:
        codigo_qr = (
            CodigoQR.objects
            .select_related('vehiculo__propietario')
            .get(contenido=token)
        )
    except CodigoQR.DoesNotExist:
        return ResultadoValidacion(autorizado=False, mensaje=CODIGO_NO_VALIDO)

    return _registrar(codigo_qr, usuario)


def validar_por_placa(placa, usuario):
    """
    Respaldo cuando el QR está dañado: mismas reglas que `validar_acceso`.
    Si la placa no existe no se guarda nada (un movimiento necesita un vehículo y su QR).
    """
    buscada = normalizar_placa(placa)
    codigo_qr = None
    if buscada:
        codigo_qr = (
            CodigoQR.objects
            .select_related('vehiculo__propietario')
            .annotate(placa_limpia=Replace('vehiculo__placa', Value('-'), Value('')))
            .filter(placa_limpia__iexact=buscada)
            .first()
        )
    if codigo_qr is None:
        return ResultadoValidacion(autorizado=False, mensaje=PLACA_NO_REGISTRADA, manual=True)

    return _registrar(codigo_qr, usuario, manual=True)
