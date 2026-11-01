"""Pruebas de las páginas de error con la marca (403, 404 y 500)."""
import tempfile

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.views.defaults import server_error

from apps.core.roles import PERSONAL_SEGURIDAD
from apps.usuarios.models import Rol


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PaginasDeErrorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guardia = get_user_model().objects.create_user(
            username='gua', email='gua@example.com', cedula='0900000002', password='Clave12345!',
            first_name='Víctor', last_name='Morán', rol=Rol.objects.create(nombre=PERSONAL_SEGURIDAD))

    def test_403_usa_la_plantilla_con_la_marca_y_vuelve_al_panel(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:configuracion_qr'))        # solo del administrador
        self.assertEqual(respuesta.status_code, 403)
        self.assertTemplateUsed(respuesta, '403.html')
        for texto in ('No tienes permiso para entrar aquí', 'Error 403', 'GaritaQR', 'Volver al panel'):
            self.assertContains(respuesta, texto, status_code=403)
        self.assertContains(respuesta, f'href="{reverse("usuarios:dashboard")}"', status_code=403)
        self.assertNotContains(respuesta, 'Iniciar sesión', status_code=403)

    def test_404_usa_la_plantilla_con_la_marca(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get('/esta-pagina-no-existe/')
        self.assertEqual(respuesta.status_code, 404)
        self.assertTemplateUsed(respuesta, '404.html')
        for texto in ('No encontramos esa página', 'Error 404', 'Volver al panel'):
            self.assertContains(respuesta, texto, status_code=404)

    def test_404_de_un_registro_que_no_existe(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:detalle', args=[99999]))
        self.assertEqual(respuesta.status_code, 404)
        self.assertTemplateUsed(respuesta, '404.html')

    def test_sin_sesion_el_boton_lleva_a_iniciar_sesion(self):
        respuesta = self.client.get('/esta-pagina-no-existe/')
        self.assertTemplateUsed(respuesta, '404.html')
        self.assertContains(respuesta, 'Iniciar sesión', status_code=404)
        self.assertContains(respuesta, f'href="{reverse("usuarios:login")}"', status_code=404)
        self.assertNotContains(respuesta, 'Volver al panel', status_code=404)

    def test_500_se_dibuja_sin_sesion_ni_contexto(self):
        respuesta = server_error(RequestFactory().get('/'))
        self.assertEqual(respuesta.status_code, 500)
        contenido = respuesta.content.decode()
        for texto in ('Algo salió mal de nuestro lado', 'Error 500', 'Volver al panel', 'GaritaQR'):
            self.assertIn(texto, contenido)

    def test_las_paginas_de_error_no_dependen_de_bootstrap_ni_de_cdn(self):
        for plantilla in ('403.html', '404.html', '500.html'):
            html = render_to_string(plantilla)
            self.assertNotIn('bootstrap', html.lower(), plantilla)
            self.assertNotIn('https://', html, plantilla)                  # nada que cargar de internet
            self.assertIn('lang="es-ec"', html)
