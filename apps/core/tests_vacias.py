"""Pantallas vacías: sin datos y sin resultados, cada lista explica qué pasa en vez de mostrar una tabla sin nada."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.roles import ADMINISTRADOR
from apps.propietarios.models import Propietario
from apps.usuarios.models import Rol
from apps.vehiculos.models import Vehiculo


class PantallasVaciasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_user(
            username='adm', email='adm@example.com', cedula='0900000001', password='Clave12345!',
            first_name='Carlos', last_name='Mendoza', rol=Rol.objects.create(nombre=ADMINISTRADOR))

    def setUp(self):
        self.client.force_login(self.admin)

    # (nombre de la ruta, mensaje cuando no hay nada, parámetros de una búsqueda sin resultados, mensaje sin resultados)
    LISTAS = (
        ('propietarios:lista', 'No se encontraron propietarios', {'q': 'zzz'}, 'limpia la búsqueda'),
        ('vehiculos:lista', 'No se encontraron vehículos', {'q': 'zzz'}, 'limpia la búsqueda'),
        ('qr:lista', 'No se encontraron códigos QR', {'q': 'zzz'}, 'limpia la búsqueda'),
        ('qr:movimientos', 'Todavía no hay movimientos registrados', {'placa': 'ZZZ'}, 'No hay movimientos con esos filtros'),
        ('qr:historial', 'Todavía no hay ingresos registrados', {'placa': 'ZZZ'}, 'No hay ingresos con esos filtros'),
        ('qr:reporte_historial', 'Todavía no hay ingresos registrados', {'placa': 'ZZZ'}, 'No hay ingresos con esos filtros'),
    )

    def test_sin_datos_cada_lista_muestra_un_mensaje(self):
        for ruta, mensaje, _params, _otro in self.LISTAS:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(reverse(ruta))
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, mensaje) if ruta not in ('propietarios:lista', 'vehiculos:lista', 'qr:lista') \
                    else self.assertContains(respuesta, mensaje)

    def test_sin_datos_las_listas_de_gestion_invitan_a_crear_el_primero(self):
        self.assertContains(self.client.get(reverse('propietarios:lista')), 'Aún no hay propietarios')
        self.assertContains(self.client.get(reverse('vehiculos:lista')), 'Aún no hay vehículos')
        self.assertContains(self.client.get(reverse('qr:lista')), 'Los códigos aparecen al registrar')

    def test_con_datos_pero_sin_resultados_cada_lista_lo_explica(self):
        propietario = Propietario.objects.create(
            nombre='Ana Mora Vera', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente')
        Vehiculo.objects.create(propietario=propietario, placa='GSA-3841', marca='Kia', modelo='Rio', color='Gris')
        for ruta, _vacio, params, mensaje in self.LISTAS:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(reverse(ruta), params)
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, mensaje)

    def test_el_resto_de_pantallas_se_abre_sin_ningun_dato(self):
        for ruta in ('usuarios:dashboard', 'qr:validar', 'qr:configuracion_qr', 'qr:reporte_historial_datos'):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 200)

    def test_validar_sin_accesos_dice_que_aun_no_hay(self):
        respuesta = self.client.get(reverse('qr:validar'))
        self.assertContains(respuesta, 'Todavía no hay accesos hoy')
        self.assertContains(respuesta, 'Aún no se ha validado ningún vehículo hoy')

    def test_el_panel_sin_movimientos_lo_explica(self):
        respuesta = self.client.get(reverse('usuarios:dashboard'))
        self.assertContains(respuesta, 'No hay movimientos registrados hoy')
        self.assertContains(respuesta, 'Aún no hay accesos registrados hoy')

    def test_los_graficos_de_reportes_tienen_mensaje_para_cuando_no_hay_ingresos(self):
        respuesta = self.client.get(reverse('qr:reporte_historial'))
        self.assertContains(respuesta, 'No hay ingresos para graficar con estos filtros.')
        datos = self.client.get(reverse('qr:reporte_historial_datos')).json()
        self.assertEqual((datos['labels'], datos['labels_validador'], datos['total']), ([], [], 0))
