from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.roles import PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.models import CodigoQR, ConfiguracionQR, HistorialIngreso, RegistroMovimiento
from apps.qr.services.validacion import extraer_token
from apps.usuarios.models import Rol
from apps.vehiculos.models import Vehiculo


class ConfiguracionQRTests(TestCase):
    def test_get_solo_crea_un_unico_registro(self):
        config = ConfiguracionQR.get_solo()
        config.expiration_days = 45
        config.save()

        misma = ConfiguracionQR.get_solo()
        self.assertEqual(misma.pk, 1)
        self.assertEqual(misma.expiration_days, 45)


class ExtraerTokenTests(TestCase):
    TOKEN = '3f2b8c9e-1d4a-4b6f-9e2a-7c5d8f1a2b3c'

    def test_acepta_token_solo(self):
        self.assertEqual(extraer_token(self.TOKEN), self.TOKEN)

    def test_acepta_signo_mas_al_inicio(self):
        self.assertEqual(extraer_token(f'+{self.TOKEN}'), self.TOKEN)

    def test_acepta_url_completa(self):
        url = f'http://localhost:8000/qr/validar/?token={self.TOKEN}'
        self.assertEqual(extraer_token(url), self.TOKEN)

    def test_texto_invalido_devuelve_none(self):
        self.assertIsNone(extraer_token('hola-no-soy-un-uuid'))
        self.assertIsNone(extraer_token(''))


class ValidarAccesoTests(TestCase):
    def setUp(self):
        rol = Rol.objects.create(nombre=PERSONAL_SEGURIDAD)
        self.guardia = get_user_model().objects.create_user(
            username='guardia', email='guardia@unemi.edu.ec', cedula='0102030405',
            password='Clave12345!', rol=rol,
        )
        self.propietario = Propietario.objects.create(
            nombre='Juan Pérez', numero_identidad='1234567890', celular='0999999999',
            correo='juan@example.com', tipo='Estudiante',
        )
        self.vehiculo = Vehiculo.objects.create(
            propietario=self.propietario, placa='ABC-1234', marca='Toyota',
            modelo='Corolla', color='Blanco', estado=Vehiculo.AUTORIZADO,
        )
        self.codigo = self.vehiculo.codigo_qr   # creado por la señal
        self.url = reverse('qr:validar')

    def validar(self):
        return self.client.get(self.url, {'token': str(self.codigo.contenido)})

    def test_la_senal_crea_el_qr_con_imagen(self):
        self.assertIsInstance(self.codigo, CodigoQR)
        self.assertTrue(self.codigo.imagen)

    def test_requiere_iniciar_sesion(self):
        respuesta = self.validar()
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(RegistroMovimiento.objects.count(), 0)

    def test_ingreso_y_salida_alternan(self):
        self.client.force_login(self.guardia)

        respuesta = self.validar()
        self.assertContains(respuesta, 'Acceso Autorizado')
        self.assertEqual(HistorialIngreso.objects.count(), 1)

        self.validar()
        ultimo = RegistroMovimiento.objects.order_by('-fecha', '-pk').first()
        self.assertEqual(ultimo.tipo, RegistroMovimiento.SALIDA)
        self.assertEqual(ultimo.usuario_validador, self.guardia)

    def test_vehiculo_suspendido_es_denegado(self):
        self.vehiculo.cambiar_estado(Vehiculo.SUSPENDIDO)
        self.client.force_login(self.guardia)

        self.validar()
        movimiento = RegistroMovimiento.objects.get()
        self.assertEqual(movimiento.estado, RegistroMovimiento.DENEGADO)
        self.assertEqual(HistorialIngreso.objects.count(), 0)

    def test_propietario_inactivo_es_denegado(self):
        self.propietario.desactivar()
        self.client.force_login(self.guardia)

        self.validar()
        self.assertEqual(RegistroMovimiento.objects.get().estado, RegistroMovimiento.DENEGADO)

    def test_qr_expirado_es_denegado_y_se_desactiva(self):
        CodigoQR.objects.filter(pk=self.codigo.pk).update(
            fecha_expiracion=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.guardia)

        self.validar()
        self.codigo.refresh_from_db()
        self.assertFalse(self.codigo.activo)
        self.assertEqual(RegistroMovimiento.objects.get().estado, RegistroMovimiento.DENEGADO)

    def test_token_invalido_no_rompe_la_pagina(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(self.url, {'token': 'texto-cualquiera'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Código no válido')

    def test_renovar_solo_acepta_post(self):
        self.client.force_login(self.guardia)
        url = reverse('qr:renovar', args=[self.codigo.pk])
        token_anterior = self.codigo.contenido

        self.assertEqual(self.client.get(url).status_code, 405)

        self.client.post(url)
        self.codigo.refresh_from_db()
        self.assertNotEqual(self.codigo.contenido, token_anterior)
