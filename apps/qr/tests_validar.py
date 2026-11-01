"""Pruebas de la Fase 6: validar acceso (QR y placa a mano), pantallas de resultado y accesos recientes."""
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.roles import PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.models import CodigoQR, ConfiguracionQR, HistorialIngreso, RegistroMovimiento
from apps.qr.services.garita import ultimos_accesos
from apps.qr.services.validacion import (
    DETALLE_MANUAL, PLACA_NO_REGISTRADA, normalizar_placa, validar_acceso, validar_por_placa)
from apps.usuarios.models import Rol
from apps.vehiculos.models import Vehiculo


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BaseValidarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guardia = get_user_model().objects.create_user(
            username='vmoran', email='vmoran@unemi.edu.ec', cedula='0900000002', password='Clave12345!',
            first_name='Víctor', last_name='Morán', rol=Rol.objects.create(nombre=PERSONAL_SEGURIDAD))
        cls.propietario = Propietario.objects.create(
            nombre='Ana Mora Vera', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente')
        cls.vehiculo = Vehiculo.objects.create(
            propietario=cls.propietario, placa='GSA-3841', marca='Toyota', modelo='Hilux',
            color='Blanco', anio=2022, estado=Vehiculo.AUTORIZADO)
        cls.codigo = cls.vehiculo.codigo_qr

    def setUp(self):
        # El vehículo se recarga: los tests cambian su estado y no deben contaminarse entre sí
        self.vehiculo.refresh_from_db()
        self.codigo.refresh_from_db()

    def ultimo_movimiento(self):
        return RegistroMovimiento.objects.order_by('-fecha', '-pk').first()


class ValidarPorPlacaServicioTests(BaseValidarTests):
    def test_normaliza_la_placa(self):
        for escrito in ('GSA-3841', 'gsa-3841', ' gsa 3841 ', 'GSA3841'):
            self.assertEqual(normalizar_placa(escrito), 'GSA3841')

    def test_autorizada_registra_ingreso_con_detalle_manual(self):
        resultado = validar_por_placa('GSA-3841', self.guardia)
        self.assertTrue(resultado.autorizado)
        self.assertTrue(resultado.manual)
        self.assertEqual(resultado.tipo, RegistroMovimiento.INGRESO)
        movimiento = RegistroMovimiento.objects.get()
        self.assertEqual(movimiento.estado, RegistroMovimiento.AUTORIZADO)
        self.assertEqual(movimiento.detalle, DETALLE_MANUAL)
        self.assertEqual(movimiento.detalle, 'Validación manual por placa')
        self.assertEqual(movimiento.usuario_validador, self.guardia)
        self.assertEqual(HistorialIngreso.objects.count(), 1)

    def test_acepta_la_placa_escrita_de_cualquier_forma(self):
        for escrito in ('gsa-3841', 'GSA 3841', 'gsa3841'):
            self.assertTrue(validar_por_placa(escrito, self.guardia).autorizado, escrito)

    def test_ingreso_y_salida_alternan_igual_que_con_el_qr(self):
        validar_acceso(str(self.codigo.contenido), self.guardia)           # ingreso por QR
        resultado = validar_por_placa('GSA-3841', self.guardia)            # ahora toca salida
        self.assertEqual(resultado.tipo, RegistroMovimiento.SALIDA)
        self.assertEqual(HistorialIngreso.objects.count(), 1)              # la salida no cuenta como ingreso

    def test_placa_no_registrada(self):
        resultado = validar_por_placa('ZZZ-0000', self.guardia)
        self.assertFalse(resultado.autorizado)
        self.assertEqual(resultado.mensaje, 'Placa no registrada')
        self.assertEqual(resultado.mensaje, PLACA_NO_REGISTRADA)
        self.assertIsNone(resultado.vehiculo)
        self.assertEqual(RegistroMovimiento.objects.count(), 0)

    def test_placa_vacia_no_registrada(self):
        self.assertEqual(validar_por_placa('   ', self.guardia).mensaje, 'Placa no registrada')

    def test_mismas_reglas_y_mismos_motivos_que_el_qr(self):
        casos = {
            'Vehículo suspendido': lambda: self.vehiculo.cambiar_estado(Vehiculo.SUSPENDIDO),
            'Vehículo no autorizado': lambda: self.vehiculo.cambiar_estado(Vehiculo.NO_AUTORIZADO),
            'Propietario inactivo': lambda: self.propietario.desactivar(),
            'Código desactivado': lambda: CodigoQR.objects.filter(pk=self.codigo.pk).update(activo=False),
            'Código expirado': lambda: CodigoQR.objects.filter(pk=self.codigo.pk).update(
                fecha_expiracion=timezone.now() - timedelta(days=1)),
        }
        def desde_cero(preparar):
            """Todo en regla y luego el problema de este caso (validar un QR vencido lo desactiva, por eso se repite)."""
            self.vehiculo.refresh_from_db()
            self.propietario.refresh_from_db()
            CodigoQR.objects.filter(pk=self.codigo.pk).update(
                activo=True, fecha_expiracion=timezone.now() + timedelta(days=30))
            self.vehiculo.cambiar_estado(Vehiculo.AUTORIZADO)
            self.propietario.activar()
            preparar()

        for motivo, preparar in casos.items():
            with self.subTest(motivo=motivo):
                desde_cero(preparar)
                por_placa = validar_por_placa('GSA-3841', self.guardia)
                self.assertFalse(por_placa.autorizado)
                self.assertEqual(por_placa.mensaje, motivo)
                self.assertEqual(self.ultimo_movimiento().detalle, motivo)   # el denegado guarda el motivo real
                self.assertEqual(self.ultimo_movimiento().estado, RegistroMovimiento.DENEGADO)

                desde_cero(preparar)
                self.assertEqual(validar_acceso(str(self.codigo.contenido), self.guardia).mensaje, motivo)

    def test_validacion_de_qr_deshabilitada_tambien_deniega_por_placa(self):
        configuracion = ConfiguracionQR.get_solo()
        configuracion.activar_qr = False
        configuracion.save()
        resultado = validar_por_placa('GSA-3841', self.guardia)
        self.assertFalse(resultado.autorizado)
        self.assertEqual(resultado.mensaje, 'Validación de QR deshabilitada')

    def test_un_qr_vencido_se_marca_inactivo_tambien_por_placa(self):
        CodigoQR.objects.filter(pk=self.codigo.pk).update(fecha_expiracion=timezone.now() - timedelta(hours=1))
        validar_por_placa('GSA-3841', self.guardia)
        self.codigo.refresh_from_db()
        self.assertFalse(self.codigo.activo)


class AccesosRecientesTests(BaseValidarTests):
    def crear_movimiento(self, fecha):
        movimiento = RegistroMovimiento.objects.create(
            codigo_qr=self.codigo, vehiculo=self.vehiculo, estado=RegistroMovimiento.AUTORIZADO,
            usuario_validador=self.guardia)
        RegistroMovimiento.objects.filter(pk=movimiento.pk).update(fecha=fecha)
        return movimiento

    def test_solo_hoy_los_mas_recientes_primero_y_con_limite(self):
        # Las fechas se arman desde la medianoche de hoy, así la prueba no depende de la hora en que corra
        inicio = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        self.crear_movimiento(inicio - timedelta(hours=1))            # ayer: no cuenta
        de_hoy = [self.crear_movimiento(inicio + timedelta(minutes=n)) for n in range(1, 8)]
        accesos = ultimos_accesos(limite=5, ahora=inicio + timedelta(hours=12))
        self.assertEqual([m.pk for m in accesos], [m.pk for m in reversed(de_hoy)][:5])

    def test_sin_movimientos_devuelve_lista_vacia(self):
        self.assertEqual(ultimos_accesos(), [])


class PantallaValidarTests(BaseValidarTests):
    def test_requiere_iniciar_sesion(self):
        for parametros in ({}, {'placa': 'GSA-3841'}, {'token': str(self.codigo.contenido)}):
            self.assertEqual(self.client.get(reverse('qr:validar'), parametros).status_code, 302)
        self.assertEqual(RegistroMovimiento.objects.count(), 0)

    def test_pantalla_principal_con_escaner_ingreso_manual_y_guardia(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'))
        self.assertEqual(respuesta.status_code, 200)
        for texto in ('Validar acceso vehicular', 'Ingreso manual por placa', 'Consultar y validar placa',
                      'Volver al menú', 'Víctor Morán', 'Guardia en turno', 'id="lector"',
                      'Todavía no hay accesos hoy'):
            self.assertContains(respuesta, texto)

    def test_la_libreria_del_escaner_tiene_version_fija(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'))
        self.assertContains(respuesta, 'cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js')
        # al leer, valida una sola vez y se vuelve a esta misma pantalla con ?token=
        self.assertContains(respuesta, 'yaLeido')
        self.assertContains(respuesta, "'?token=' + encodeURIComponent(texto)")

    def test_mensajes_claros_si_no_hay_camara_o_permiso(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'))
        for texto in ('no tiene permiso para usar la cámara', 'No se encontró ninguna cámara',
                      'localhost o con HTTPS', 'seguir validando con la placa', 'Reintentar cámara'):
            self.assertContains(respuesta, texto)

    def test_muestra_el_ultimo_resultado_y_los_accesos_de_hoy(self):
        self.client.force_login(self.guardia)
        self.client.get(reverse('qr:validar'), {'placa': 'GSA-3841'})
        respuesta = self.client.get(reverse('qr:validar'))
        self.assertContains(respuesta, 'Último acceso procesado')
        self.assertContains(respuesta, 'AUTORIZADO')
        self.assertContains(respuesta, 'Últimos accesos de hoy')
        self.assertContains(respuesta, 'GSA-3841')
        self.assertContains(respuesta, 'Ana Mora Vera')

    def test_placa_en_blanco_pide_la_placa_y_no_registra_nada(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'placa': '   '})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Escribe la placa del vehículo.')
        self.assertEqual(RegistroMovimiento.objects.count(), 0)

    def test_sin_datos_inventados(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'))
        for texto in ('Carril', 'Sanciones', 'Registrar incidencia', 'FPS', 'Latencia', 'Comprobante',
                      'Terminal activa', 'Sentido del tránsito'):
            self.assertNotContains(respuesta, texto)


class ResultadoAutorizadoTests(BaseValidarTests):
    def validar_placa(self):
        self.client.force_login(self.guardia)
        return self.client.get(reverse('qr:validar'), {'placa': 'GSA-3841'})

    def test_muestra_los_datos_reales_del_ingreso(self):
        respuesta = self.validar_placa()
        self.assertTemplateUsed(respuesta, 'qr/validar_success.html')
        movimiento = RegistroMovimiento.objects.get()
        hora = timezone.localtime(movimiento.fecha).strftime('%H:%M:%S')
        for texto in ('Ingreso autorizado', 'GSA-3841', 'Toyota Hilux', 'Blanco', '2022', 'Ana Mora Vera',
                      '0912345678', 'Docente', 'Validó: Víctor Morán', hora, 'Validación manual por placa',
                      'Validar otro vehículo', 'Volver al menú', 'día', 'restante'):
            self.assertContains(respuesta, texto)
        self.assertContains(respuesta, reverse('qr:detalle', args=[self.codigo.pk]))

    def test_el_segundo_movimiento_es_una_salida(self):
        self.validar_placa()
        respuesta = self.validar_placa()
        self.assertContains(respuesta, 'Salida autorizada')
        self.assertNotContains(respuesta, 'Ingreso autorizado')

    def test_con_qr_no_dice_validacion_manual(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'token': str(self.codigo.contenido)})
        self.assertTemplateUsed(respuesta, 'qr/validar_success.html')
        self.assertNotContains(respuesta, 'Validación manual por placa')
        self.assertEqual(RegistroMovimiento.objects.get().detalle, 'Acceso autorizado')

    def test_no_incluye_datos_que_el_sistema_no_tiene(self):
        respuesta = self.validar_placa()
        for texto in ('Carril', 'Sanciones', 'Matrícula vinculada', 'Registrar incidencia'):
            self.assertNotContains(respuesta, texto)

    def test_deja_la_direccion_limpia_para_que_recargar_no_valide_otra_vez(self):
        self.assertContains(self.validar_placa(), 'history.replaceState(null')


class ResultadoDenegadoTests(BaseValidarTests):
    def test_vehiculo_suspendido_muestra_el_motivo_y_los_datos(self):
        self.vehiculo.cambiar_estado(Vehiculo.SUSPENDIDO)
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'token': str(self.codigo.contenido)})
        self.assertTemplateUsed(respuesta, 'qr/validar_failure.html')
        for texto in ('Acceso denegado', 'Causa del rechazo', 'Vehículo suspendido', 'GSA-3841', 'Toyota Hilux',
                      'Ana Mora Vera', 'Suspendido', 'Validó: Víctor Morán', 'Validar otro vehículo',
                      'Intento de ingreso'):
            self.assertContains(respuesta, texto)
        self.assertNotContains(respuesta, 'Vehículo acceso suspendido')
        self.assertEqual(RegistroMovimiento.objects.get().detalle, 'Vehículo suspendido')

    def test_codigo_expirado_muestra_la_fecha_de_expiracion(self):
        vencio = timezone.now() - timedelta(days=2)
        CodigoQR.objects.filter(pk=self.codigo.pk).update(fecha_expiracion=vencio)
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'placa': 'GSA-3841'})
        self.assertContains(respuesta, 'Código expirado')
        self.assertContains(respuesta, 'Expirada el ' + timezone.localtime(vencio).strftime('%d/%m/%Y'))
        self.assertContains(respuesta, 'Validación manual por placa')
        self.assertNotContains(respuesta, 'Validar por placa')     # ya se validó a mano

    def test_propietario_inactivo(self):
        self.propietario.desactivar()
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'placa': 'GSA-3841'})
        self.assertContains(respuesta, 'Propietario inactivo')

    def test_placa_no_registrada_no_inventa_datos(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'placa': 'ZZZ-0000'})
        self.assertTemplateUsed(respuesta, 'qr/validar_failure.html')
        self.assertContains(respuesta, 'Placa no registrada')
        self.assertContains(respuesta, 'Validar otro vehículo')
        self.assertNotContains(respuesta, 'Vehículo registrado')
        self.assertEqual(RegistroMovimiento.objects.count(), 0)

    def test_codigo_no_valido_ofrece_validar_por_placa(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'token': 'texto-cualquiera'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Código no válido')
        self.assertContains(respuesta, 'Validar por placa')

    def test_no_incluye_datos_que_el_sistema_no_tiene(self):
        self.vehiculo.cambiar_estado(Vehiculo.SUSPENDIDO)
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:validar'), {'placa': 'GSA-3841'})
        for texto in ('Carril', 'Sanciones', 'Matrícula vinculada', 'Registrar incidencia', 'barrera'):
            self.assertNotContains(respuesta, texto)
