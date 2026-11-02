from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD
from apps.usuarios.models import Rol


class UsuariosViewsTests(TestCase):
    def setUp(self):
        self.rol = Rol.objects.create(nombre=ADMINISTRADOR)
        self.user = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            cedula='0912345678',
            password='Admin12345!',
            rol=self.rol,
        )

    def test_login_con_usuario_y_acceso_al_dashboard(self):
        self.assertTrue(self.client.login(username='admin', password='Admin12345!'))
        respuesta = self.client.get('/dashboard/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Panel de control')

    def test_login_con_correo_redirige_al_dashboard(self):
        respuesta = self.client.post('/login/', {
            'username': 'ADMIN@example.com',     # tampoco importan mayúsculas
            'password': 'Admin12345!',
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, '/dashboard/')

    def test_login_con_clave_incorrecta_no_entra(self):
        respuesta = self.client.post('/login/', {'username': 'admin', 'password': 'mala'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_redirige_al_login(self):
        self.client.login(username='admin', password='Admin12345!')
        respuesta = self.client.post('/logout/')
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/login/', respuesta.url)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_por_get_no_cierra_la_sesion(self):
        self.client.login(username='admin', password='Admin12345!')
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_sin_recordarme_termina_al_cerrar_el_navegador(self):
        self.client.post('/login/', {'username': 'admin', 'password': 'Admin12345!'})
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_con_recordarme_mantiene_la_sesion(self):
        self.client.post('/login/', {
            'username': 'admin', 'password': 'Admin12345!', 'recordarme': 'on',
        })
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_menu_muestra_configuracion_solo_al_administrador(self):
        enlace = 'href="/qr/configuracion/"'
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/dashboard/'), enlace)

        rol_seg = Rol.objects.create(nombre=PERSONAL_SEGURIDAD)
        guardia = get_user_model().objects.create_user(
            username='guardia', email='guardia@example.com', cedula='0911111111',
            password='Guardia12345!', rol=rol_seg,
        )
        self.client.force_login(guardia)
        respuesta = self.client.get('/dashboard/')
        self.assertNotContains(respuesta, enlace)      # ni en el menú ni en el panel
        self.assertContains(respuesta, 'Personal Seguridad')

    def test_paginas_no_muestran_comentarios_de_plantilla_ni_texto_suelto(self):
        # {# #} de varias líneas se imprime tal cual en la página
        self.assertNotContains(self.client.get('/login/'), '{#')
        self.client.force_login(self.user)
        for url in ('/dashboard/', '/propietarios/', '/vehiculos/', '/qr/'):
            self.assertNotContains(self.client.get(url), '{#')

    def test_menu_muestra_el_rol_completo(self):
        rol_seg = Rol.objects.create(nombre=PERSONAL_SEGURIDAD)
        guardia = get_user_model().objects.create_user(
            username='guardia2', email='guardia2@example.com', cedula='0922222222',
            password='Guardia12345!', rol=rol_seg,
        )
        self.client.force_login(guardia)
        respuesta = self.client.get('/dashboard/')
        self.assertContains(respuesta, 'Personal Seguridad')   # el rol entero, sin truncar
        self.assertContains(respuesta, 'Cerrar sesión')

    def test_barra_superior_muestra_fecha_y_buscador_de_placa(self):
        self.client.force_login(self.user)
        respuesta = self.client.get('/dashboard/')
        self.assertContains(respuesta, 'Sistema activo')
        self.assertContains(respuesta, 'name="q"')

    def test_raiz_redirige_segun_sesion(self):
        self.assertIn('/login/', self.client.get('/').url)
        self.client.login(username='admin', password='Admin12345!')
        self.assertEqual(self.client.get('/').url, '/dashboard/')

    def test_usuario_sin_rol_no_entra_a_vehiculos(self):
        sin_rol = get_user_model().objects.create_user(
            username='visita', email='visita@example.com', cedula='0999999990', password='Visita12345!',
        )
        self.client.force_login(sin_rol)
        self.assertEqual(self.client.get('/vehiculos/').status_code, 403)


class IncludesYFiltrosTests(TestCase):
    def test_iniciales(self):
        from apps.core.templatetags.ui import iniciales
        self.assertEqual(iniciales('Juan Carlos Pérez'), 'JC')
        self.assertEqual(iniciales('admin'), 'A')
        self.assertEqual(iniciales(''), '?')
        self.assertEqual(iniciales(None), '?')

    def test_include_placa_y_badge(self):
        from django.template.loader import render_to_string
        placa = render_to_string('includes/placa.html', {'placa': 'GSA-3841'})
        self.assertIn('GSA-3841', placa)
        self.assertIn('Ecuador', placa)
        badge = render_to_string('includes/badge_estado.html', {'texto': 'Autorizado', 'tono': 'verde'})
        self.assertIn('Autorizado', badge)
        self.assertIn('emerald', badge)
