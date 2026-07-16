from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.usuarios.models import Rol


class UsuariosViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role = Rol.objects.create(nombre='Administrador')
        self.user = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            rol=self.role,
        )

    def test_login_and_dashboard_access(self):
        login_ok = self.client.login(username='admin', password='admin123')
        self.assertTrue(login_ok)

        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel de Control')

    def test_root_redirects_to_login_for_anonymous_user(self):
        response = self.client.get('/', follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/')

    def test_logout_redirects_to_login(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
