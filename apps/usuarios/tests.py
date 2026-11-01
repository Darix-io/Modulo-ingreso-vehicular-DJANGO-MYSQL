from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.roles import ADMINISTRADOR
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
        self.assertContains(respuesta, 'Panel de Control')

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
        respuesta = self.client.get('/logout/')
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/login/', respuesta.url)

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
