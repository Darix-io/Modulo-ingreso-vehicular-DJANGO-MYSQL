from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.propietarios.models import Propietario
from apps.qr.models import ConfiguracionQR, CodigoQR
from apps.vehiculos.models import Vehiculo


class ConfiguracionQRTests(TestCase):
    def test_get_solo_creates_singleton(self):
        config = ConfiguracionQR.get_solo()
        self.assertIsNotNone(config)
        self.assertEqual(config.id, 1)

        config.expiration_days = 45
        config.save()

        same_config = ConfiguracionQR.get_solo()
        self.assertEqual(same_config.id, config.id)
        self.assertEqual(same_config.expiration_days, 45)

    def test_get_solo_returns_existing(self):
        first = ConfiguracionQR.get_solo()
        second = ConfiguracionQR.get_solo()
        self.assertEqual(first.pk, second.pk)


class ValidarAccesoQrTests(TestCase):
    def test_validar_accepts_token_with_leading_plus(self):
        propietario = Propietario.objects.create(
            nombre='Juan Pérez',
            numero_identidad='1234567890',
            celular='0999999999',
            correo='juan@example.com',
            tipo='Estudiante',
        )
        vehiculo = Vehiculo.objects.create(
            propietario=propietario,
            placa='ABC-1234',
            marca='Toyota',
            modelo='Corolla',
            color='Blanco',
            estado='AUTORIZADO',
        )
        codigo_qr = vehiculo.codigo_qr
        codigo_qr.fecha_expiracion = timezone.now() + timedelta(days=1)
        codigo_qr.save(update_fields=['fecha_expiracion'])

        response = self.client.get(f'/qr/validar/?token=+{codigo_qr.contenido}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acceso Autorizado')
