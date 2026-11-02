"""Generación de la imagen PNG del código QR."""
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse


def construir_url_validacion(token):
    """URL que se guarda dentro del QR. Al escanearlo, el celular la abre."""
    base_url = getattr(settings, 'VALIDACION_URL_BASE', '').rstrip('/')
    if not base_url:
        return str(token)
    return f"{base_url}{reverse('qr:validar')}?token={token}"


def generar_imagen_qr(codigo_qr):
    """
    Crea la imagen del QR y la asigna al campo `imagen` del objeto.
    No guarda en la BD (eso lo hace CodigoQR.save()).
    """
    token = str(codigo_qr.contenido)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(construir_url_validacion(token))
    qr.make(fit=True)
    imagen = qr.make_image(fill_color='black', back_color='white')

    buffer = BytesIO()
    imagen.save(buffer, format='PNG')

    nombre_archivo = f'qr_{codigo_qr.vehiculo.placa}_{token[:8]}.png'
    codigo_qr.imagen.save(nombre_archivo, ContentFile(buffer.getvalue()), save=False)
