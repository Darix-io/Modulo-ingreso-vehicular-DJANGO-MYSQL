"""Pruebas de la Fase 8: Configuración QR (permisos, guardado, validación y renovación automática)."""
import tempfile
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.forms import ConfiguracionQRForm
from apps.qr.models import CodigoQR, ConfiguracionQR
from apps.qr.services.mantenimiento import ejecutar_mantenimiento
from apps.qr.validadores import DIAS_MAXIMO, DIAS_MINIMO, validar_dias_vigencia
from apps.usuarios.models import Rol
from apps.vehiculos.models import Vehiculo


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BaseConfiguracionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        cls.admin = Usuario.objects.create_user(
            username='adm', email='adm@example.com', cedula='0900000001', password='Clave12345!',
            first_name='Carlos', last_name='Mendoza', rol=Rol.objects.create(nombre=ADMINISTRADOR))
        cls.guardia = Usuario.objects.create_user(
            username='gua', email='gua@example.com', cedula='0900000002', password='Clave12345!',
            first_name='Víctor', last_name='Morán', rol=Rol.objects.create(nombre=PERSONAL_SEGURIDAD))
        cls.propietario = Propietario.objects.create(
            nombre='Ana Mora Vera', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente')

    def vehiculo(self, placa, estado=Vehiculo.AUTORIZADO, propietario=None):
        return Vehiculo.objects.create(
            propietario=propietario or self.propietario, placa=placa, marca='Kia', modelo='Rio',
            color='Gris', estado=estado)

    def vencer(self, vehiculo, dias=2):
        CodigoQR.objects.filter(vehiculo=vehiculo).update(
            fecha_expiracion=timezone.now() - timedelta(days=dias),
            fecha_creacion=timezone.now() - timedelta(days=dias + 30))
        return CodigoQR.objects.get(vehiculo=vehiculo)


class PermisosConfiguracionTests(BaseConfiguracionTests):
    def test_anonimo_va_al_login(self):
        self.assertEqual(self.client.get(reverse('qr:configuracion_qr')).status_code, 302)
        self.assertEqual(self.client.post(reverse('qr:configuracion_qr'), {'expiration_days': 10}).status_code, 302)

    def test_seguridad_recibe_403_al_ver_y_al_guardar_y_nada_cambia(self):
        self.client.force_login(self.guardia)
        url = reverse('qr:configuracion_qr')
        self.assertEqual(self.client.get(url).status_code, 403)
        respuesta = self.client.post(url, {'expiration_days': 5, 'activar_qr': ''})
        self.assertEqual(respuesta.status_code, 403)
        configuracion = ConfiguracionQR.get_solo()
        self.assertEqual(configuracion.expiration_days, 30)
        self.assertTrue(configuracion.activar_qr)

    def test_el_administrador_si_entra(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('qr:configuracion_qr')).status_code, 200)

    def test_el_menu_solo_la_muestra_al_administrador(self):
        enlace = f'href="{reverse("qr:configuracion_qr")}"'
        self.client.force_login(self.guardia)
        self.assertNotContains(self.client.get(reverse('usuarios:dashboard')), enlace)
        self.assertNotContains(self.client.get(reverse('qr:lista')), enlace)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('usuarios:dashboard')), enlace)
        self.assertContains(self.client.get(reverse('qr:lista')), enlace)


class GuardarConfiguracionTests(BaseConfiguracionTests):
    url = reverse('qr:configuracion_qr')

    def guardar(self, **datos):
        self.client.force_login(self.admin)
        return self.client.post(self.url, datos)

    def test_guarda_vigencia_validacion_y_renovacion_automatica(self):
        respuesta = self.guardar(expiration_days=90, activar_qr='on', renovacion_automatica='on')
        self.assertRedirects(respuesta, self.url)
        configuracion = ConfiguracionQR.get_solo()
        self.assertEqual(configuracion.expiration_days, 90)
        self.assertTrue(configuracion.activar_qr)
        self.assertTrue(configuracion.renovacion_automatica)

    def test_un_interruptor_sin_marcar_queda_apagado(self):
        self.guardar(expiration_days=30, renovacion_automatica='on')
        configuracion = ConfiguracionQR.get_solo()
        self.assertFalse(configuracion.activar_qr)
        self.assertTrue(configuracion.renovacion_automatica)

    def test_mensaje_de_confirmacion_con_lo_guardado(self):
        respuesta = self.guardar(expiration_days=60, activar_qr='on')
        textos = [str(mensaje) for mensaje in get_messages(respuesta.wsgi_request)]
        self.assertEqual(len(textos), 1)
        self.assertIn('Configuración guardada', textos[0])
        self.assertIn('60 días', textos[0])
        self.assertIn('validación activada', textos[0])
        self.assertIn('renovación automática desactivada', textos[0])

    def test_sin_cambios_avisa_que_no_hubo_nada_que_guardar(self):
        respuesta = self.guardar(expiration_days=30, activar_qr='on')
        textos = [str(mensaje) for mensaje in get_messages(respuesta.wsgi_request)]
        self.assertEqual(textos, ['No hubo cambios que guardar.'])

    def test_vigencia_fuera_de_rango_no_se_guarda_y_explica_por_que(self):
        for dias in ('0', '366', '-5', '', 'abc'):
            respuesta = self.guardar(expiration_days=dias, activar_qr='on')
            self.assertEqual(respuesta.status_code, 200, dias)       # vuelve al formulario
            self.assertTrue(respuesta.context['form'].errors['expiration_days'], dias)
        self.assertEqual(ConfiguracionQR.get_solo().expiration_days, 30)

    def test_no_permite_cambiar_campos_que_no_son_de_esta_pantalla(self):
        self.guardar(expiration_days=45, activar_qr='on', permitir_reutilizacion='on', nombre='Otro', descripcion='x')
        configuracion = ConfiguracionQR.get_solo()
        self.assertFalse(configuracion.permitir_reutilizacion)
        self.assertEqual(configuracion.nombre, 'Configuración QR')
        self.assertEqual(set(ConfiguracionQRForm().fields), {'activar_qr', 'expiration_days', 'renovacion_automatica'})

    def test_la_nueva_vigencia_aplica_a_los_qr_que_se_crean_despues(self):
        self.guardar(expiration_days=10, activar_qr='on')
        antes = timezone.now()
        codigo = self.vehiculo('GAA-0001').codigo_qr
        dias = (codigo.fecha_expiracion - antes).total_seconds() / 86400
        self.assertAlmostEqual(dias, 10, delta=0.01)

    def test_validacion_desactivada_deniega_los_ingresos(self):
        vehiculo = self.vehiculo('GAA-0002')
        self.guardar(expiration_days=30)                               # activar_qr sin marcar = apagado
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'token': str(vehiculo.codigo_qr.contenido)})
        self.assertContains(respuesta, 'Validación de QR deshabilitada')


class ValidadorDeVigenciaTests(TestCase):
    def test_acepta_de_1_a_365(self):
        self.assertEqual(validar_dias_vigencia(DIAS_MINIMO), 1)
        self.assertEqual(validar_dias_vigencia(90), 90)
        self.assertEqual(validar_dias_vigencia(DIAS_MAXIMO), 365)

    def test_rechaza_fuera_de_rango_o_vacio(self):
        for malo in (0, -1, 366, 10_000, None):
            with self.assertRaises(ValidationError, msg=str(malo)):
                validar_dias_vigencia(malo)


class MantenimientoTests(BaseConfiguracionTests):
    def activar_renovacion(self, valor=True):
        configuracion = ConfiguracionQR.get_solo()
        configuracion.renovacion_automatica = valor
        configuracion.save()

    def test_por_defecto_expira_pero_no_renueva(self):
        codigo = self.vencer(self.vehiculo('GAA-0001'))
        expirados, renovados, se_renovo = ejecutar_mantenimiento()
        codigo.refresh_from_db()
        self.assertEqual((expirados, renovados, se_renovo), (1, 0, False))
        self.assertFalse(codigo.activo)

    def test_con_renovacion_automatica_renueva_los_de_vehiculos_autorizados(self):
        codigo = self.vencer(self.vehiculo('GAA-0001'))
        token = codigo.contenido
        self.activar_renovacion()
        expirados, renovados, se_renovo = ejecutar_mantenimiento()
        codigo.refresh_from_db()
        self.assertEqual((expirados, renovados, se_renovo), (1, 1, True))
        self.assertTrue(codigo.activo)
        self.assertFalse(codigo.is_expired)
        self.assertNotEqual(codigo.contenido, token)                    # la credencial impresa anterior deja de servir

    def test_nunca_renueva_suspendidos_no_autorizados_ni_propietarios_inactivos(self):
        suspendido = self.vencer(self.vehiculo('GAA-0002', Vehiculo.SUSPENDIDO))
        no_autorizado = self.vencer(self.vehiculo('GAA-0003', Vehiculo.NO_AUTORIZADO))
        inactivo = Propietario.objects.create(
            nombre='Luis Inactivo', numero_identidad='0933333333', celular='0993333333',
            correo='luis@unemi.edu.ec', tipo='Estudiante', estado=False)
        con_propietario_inactivo = self.vencer(self.vehiculo('GAA-0004', propietario=inactivo))
        self.activar_renovacion()
        _, renovados, _ = ejecutar_mantenimiento()
        self.assertEqual(renovados, 0)
        for codigo in (suspendido, no_autorizado, con_propietario_inactivo):
            codigo.refresh_from_db()
            self.assertTrue(codigo.is_expired)
            self.assertFalse(codigo.activo)

    def test_no_toca_los_qr_vigentes(self):
        vigente = self.vehiculo('GAA-0005').codigo_qr
        token = vigente.contenido
        self.activar_renovacion()
        self.assertEqual(ejecutar_mantenimiento()[:2], (0, 0))
        vigente.refresh_from_db()
        self.assertEqual(vigente.contenido, token)

    def test_la_opcion_renovar_fuerza_la_renovacion(self):
        codigo = self.vencer(self.vehiculo('GAA-0006'))
        self.assertEqual(ejecutar_mantenimiento(forzar_renovacion=True), (1, 1, True))
        codigo.refresh_from_db()
        self.assertTrue(codigo.activo)

    def test_el_comando_informa_lo_que_hizo(self):
        self.vencer(self.vehiculo('GAA-0007'))
        salida = StringIO()
        call_command('run_qr_maintenance', stdout=salida)
        self.assertIn('1 códigos QR marcados como expirados', salida.getvalue())
        self.assertIn('Renovación automática desactivada', salida.getvalue())

        self.activar_renovacion()
        salida = StringIO()
        call_command('run_qr_maintenance', stdout=salida)
        self.assertIn('1 códigos QR renovados', salida.getvalue())


class PanelYConfiguracionTests(BaseConfiguracionTests):
    def test_el_panel_muestra_la_renovacion_automatica_en_vez_de_la_reutilizacion(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('usuarios:dashboard'))
        self.assertContains(respuesta, 'Renovación automática')
        self.assertNotContains(respuesta, 'Reutilización')
