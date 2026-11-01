import tempfile
from datetime import datetime, time as dtime, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.models import CodigoQR, ConfiguracionQR, HistorialIngreso, RegistroMovimiento
from apps.qr.services.validacion import extraer_token
from apps.usuarios.models import Rol, Usuario
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
        self.admin = get_user_model().objects.create_user(
            username='admin_qr', email='admin_qr@unemi.edu.ec', cedula='0102030406',
            password='Clave12345!', rol=Rol.objects.create(nombre=ADMINISTRADOR),
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
        self.client.force_login(self.admin)
        url = reverse('qr:renovar', args=[self.codigo.pk])
        token_anterior = self.codigo.contenido

        self.assertEqual(self.client.get(url).status_code, 405)

        self.client.post(url)
        self.codigo.refresh_from_db()
        self.assertNotEqual(self.codigo.contenido, token_anterior)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SeedDemoTests(TestCase):
    """El comando seed_demo crea datos realistas y no se duplica."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=StringIO())

    def test_crea_propietarios_vehiculos_y_qr(self):
        self.assertEqual(Propietario.objects.count(), 15)
        self.assertEqual(set(Propietario.objects.values_list('tipo', flat=True)),
                         {'Estudiante', 'Docente', 'Administrativo', 'Visitante'})
        self.assertEqual(Vehiculo.objects.count(), 20)
        self.assertEqual(CodigoQR.objects.count(), 20)
        self.assertEqual(set(Vehiculo.objects.values_list('estado', flat=True)),
                         {Vehiculo.AUTORIZADO, Vehiculo.SUSPENDIDO, Vehiculo.NO_AUTORIZADO})
        self.assertTrue(Vehiculo.objects.filter(placa='GSA-3841').exists())

    def test_cedulas_de_10_digitos_y_celulares_validos(self):
        for propietario in Propietario.objects.all():
            self.assertRegex(propietario.numero_identidad, r'^\d{10}$')
            self.assertRegex(propietario.celular, r'^09\d{8}$')

    def test_qr_vigentes_por_vencer_y_expirados(self):
        ahora = timezone.now()
        por_vencer = CodigoQR.objects.filter(
            activo=True, fecha_expiracion__gt=ahora, fecha_expiracion__lte=ahora + timedelta(days=3))
        expirados = CodigoQR.objects.filter(fecha_expiracion__lte=ahora)
        self.assertEqual(por_vencer.count(), 3)
        self.assertEqual(expirados.count(), 3)
        self.assertFalse(expirados.filter(activo=True).exists())

    def test_movimientos_de_30_dias_con_dos_guardias(self):
        self.assertGreater(RegistroMovimiento.objects.count(), 100)
        self.assertTrue(RegistroMovimiento.objects.filter(estado=RegistroMovimiento.DENEGADO).exists())
        guardias = set(RegistroMovimiento.objects.values_list('usuario_validador__username', flat=True))
        self.assertEqual(guardias, {'seguridad', 'seguridad2'})
        mas_antiguo = RegistroMovimiento.objects.order_by('fecha').first().fecha
        self.assertGreaterEqual(mas_antiguo, timezone.now() - timedelta(days=31))
        self.assertFalse(RegistroMovimiento.objects.filter(fecha__gt=timezone.now()).exists())

    def test_historial_coincide_con_los_ingresos_autorizados(self):
        ingresos = RegistroMovimiento.objects.filter(
            estado=RegistroMovimiento.AUTORIZADO, tipo=RegistroMovimiento.INGRESO).count()
        self.assertEqual(HistorialIngreso.objects.count(), ingresos)

    def test_los_denegados_tienen_el_motivo_real_de_las_reglas(self):
        motivos = set(RegistroMovimiento.objects.filter(
            estado=RegistroMovimiento.DENEGADO).values_list('detalle', flat=True))
        permitidos = {'Código expirado', 'Código desactivado', 'Propietario inactivo',
                      'Vehículo acceso suspendido', 'Vehículo no autorizado'}
        self.assertTrue(motivos <= permitidos, motivos - permitidos)

    def test_no_duplica_al_ejecutarse_dos_veces(self):
        movimientos = RegistroMovimiento.objects.count()
        salida = StringIO()
        call_command('seed_demo', stdout=salida)
        self.assertIn('ya existen', salida.getvalue())
        self.assertEqual(Propietario.objects.count(), 15)
        self.assertEqual(Vehiculo.objects.count(), 20)
        self.assertEqual(RegistroMovimiento.objects.count(), movimientos)

    def test_usuarios_con_nombre_y_segundo_guardia(self):
        nombres = {u.username: u.get_full_name() for u in Usuario.objects.all()}
        self.assertEqual(nombres['admin'], 'Carlos Mendoza')
        self.assertEqual(nombres['seguridad'], 'Víctor Morán')
        self.assertEqual(nombres['seguridad2'], 'Luis Castro')


class ResumenDashboardTests(TestCase):
    """Los números del panel de control salen de datos reales."""

    @classmethod
    def setUpTestData(cls):
        cls.propietario = Propietario.objects.create(
            nombre='Ana Mora', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente',
        )
        cls.guardia = get_user_model().objects.create_user(
            username='g1', email='g1@example.com', cedula='0900000001', password='Clave12345!')

    def _vehiculo(self, placa, estado=Vehiculo.AUTORIZADO):
        return Vehiculo.objects.create(
            propietario=self.propietario, placa=placa, marca='Kia', modelo='Rio', color='Gris', estado=estado)

    def _movimiento(self, vehiculo, estado, detalle='', tipo=RegistroMovimiento.INGRESO):
        return RegistroMovimiento.objects.create(
            codigo_qr=vehiculo.codigo_qr, vehiculo=vehiculo, tipo=tipo, estado=estado,
            usuario_validador=self.guardia, detalle=detalle)

    def test_qr_activos_cuenta_solo_vigentes_y_no_dias_de_configuracion(self):
        from apps.qr.services.estadisticas import resumen_dashboard
        vigente = self._vehiculo('GAA-1111')
        por_vencer = self._vehiculo('GAA-2222')
        expirado = self._vehiculo('GAA-3333')
        inactivo = self._vehiculo('GAA-4444')
        ahora = timezone.now()
        CodigoQR.objects.filter(vehiculo=por_vencer).update(fecha_expiracion=ahora + timedelta(days=2))
        CodigoQR.objects.filter(vehiculo=expirado).update(fecha_expiracion=ahora - timedelta(days=1))
        CodigoQR.objects.filter(vehiculo=inactivo).update(activo=False)

        datos = resumen_dashboard()
        self.assertEqual(datos['qr_activos'], 2)          # vigente + por vencer
        self.assertEqual(datos['qr_proximos_vencer'], 1)  # el expirado no cuenta como "por vencer"

    def test_porcentajes_y_causa_frecuente_de_hoy(self):
        from apps.qr.services.estadisticas import resumen_dashboard
        v = self._vehiculo('GBB-1111')
        for _ in range(3):
            self._movimiento(v, RegistroMovimiento.AUTORIZADO)
        self._movimiento(v, RegistroMovimiento.DENEGADO, 'Código expirado')

        datos = resumen_dashboard()
        self.assertEqual(datos['autorizados_hoy'], 3)
        self.assertEqual(datos['denegados_hoy'], 1)
        self.assertEqual(datos['porcentaje_exito'], 75.0)
        self.assertEqual(datos['porcentaje_rechazo'], 25.0)
        self.assertEqual(datos['porcentaje_exito_ancho'], 75)
        self.assertEqual(datos['causa_frecuente'], ('Código expirado', 1))

    def test_sin_movimientos_no_hay_porcentajes_enganosos(self):
        from apps.qr.services.estadisticas import resumen_dashboard
        datos = resumen_dashboard()
        self.assertIsNone(datos['porcentaje_exito'])
        self.assertIsNone(datos['porcentaje_rechazo'])
        self.assertIsNone(datos['causa_frecuente'])
        self.assertEqual(datos['qr_activos'], 0)

    def test_variacion_porcentual_y_saludo(self):
        from apps.qr.services.estadisticas import _variacion_pct, saludo
        self.assertEqual(_variacion_pct(15, 10), 50.0)
        self.assertEqual(_variacion_pct(5, 10), -50.0)
        self.assertIsNone(_variacion_pct(5, 0))
        hoy = timezone.localdate()
        def a_las(hora):
            return timezone.make_aware(datetime.combine(hoy, dtime(hora)))
        self.assertEqual(saludo(a_las(9)), 'Buenos días')
        self.assertEqual(saludo(a_las(15)), 'Buenas tardes')
        self.assertEqual(saludo(a_las(21)), 'Buenas noches')

    def test_pantalla_muestra_datos_reales(self):
        rol = Rol.objects.create(nombre=PERSONAL_SEGURIDAD)
        self.guardia.rol = rol
        self.guardia.first_name = 'Víctor'
        self.guardia.save()
        v = self._vehiculo('GSA-3841')
        self._movimiento(v, RegistroMovimiento.AUTORIZADO)
        self._movimiento(v, RegistroMovimiento.DENEGADO, 'Código expirado')

        self.client.force_login(self.guardia)
        respuesta = self.client.get('/dashboard/')
        self.assertContains(respuesta, 'Víctor')
        self.assertContains(respuesta, 'GSA-3841')                 # placa en la tabla
        self.assertContains(respuesta, 'Código expirado')          # causa y detalle reales
        self.assertContains(respuesta, 'QR activos')
        self.assertNotContains(respuesta, '30 días</p>')           # ya no muestra la config como "QR activos"
        self.assertContains(respuesta, 'reportes/historial/pdf/?fecha_inicio=')
        self.assertContains(respuesta, reverse('qr:validar'))
        self.assertNotContains(respuesta, 'Ajustar parámetros')    # solo administradores

    def test_boton_de_configuracion_solo_para_administrador(self):
        rol = Rol.objects.create(nombre='Administrador')
        admin = get_user_model().objects.create_user(
            username='adm', email='adm@example.com', cedula='0900000002', password='Clave12345!', rol=rol)
        self.client.force_login(admin)
        self.assertContains(self.client.get('/dashboard/'), 'Ajustar parámetros')


class SeedDemoHoyTests(TestCase):
    """Movimientos de HOY de la demostración (con una hora simulada, no la del reloj)."""

    def _ahora_simulada(self, hora, minuto=0):
        return timezone.make_aware(datetime.combine(timezone.localdate(), dtime(hora, minuto)))

    def _vehiculos(self):
        from types import SimpleNamespace
        from apps.qr.management.commands.seed_demo import VEHICULOS
        vehiculos = [SimpleNamespace(placa=datos[0]) for datos in VEHICULOS]
        return vehiculos, [1] * len(vehiculos)

    def test_hoy_va_de_las_6_hasta_la_hora_actual_sin_futuro(self):
        import random
        from apps.qr.management.commands.seed_demo import Command
        ahora = self._ahora_simulada(15)
        vehiculos, pesos = self._vehiculos()
        eventos = Command._eventos_de_hoy(random.Random(1), vehiculos, pesos, ahora)
        self.assertGreaterEqual(len(eventos), 6)
        for momento, _vehiculo, _azar in eventos:
            self.assertGreaterEqual(momento, self._ahora_simulada(6))
            self.assertLess(momento, ahora)

    def test_hoy_incluye_los_tres_denegados_con_motivos_reales(self):
        import random
        from apps.qr.management.commands.seed_demo import Command, PLACAS_DENEGADAS_HOY
        ahora = self._ahora_simulada(15)
        vehiculos, pesos = self._vehiculos()
        eventos = Command._eventos_de_hoy(random.Random(1), vehiculos, pesos, ahora)
        placas = {vehiculo.placa for _m, vehiculo, _a in eventos}
        self.assertTrue(set(PLACAS_DENEGADAS_HOY) <= placas)
        # el QR de GAD-7712 vence hoy hacia las 11:36: su intento tiene que ser posterior
        intentos_gad = [m for m, v, _a in eventos if v.placa == 'GAD-7712']
        self.assertTrue(any(m > self._ahora_simulada(11, 36) for m in intentos_gad))

    def test_antes_de_abrir_la_jornada_no_hay_movimientos_de_hoy(self):
        import random
        from apps.qr.management.commands.seed_demo import Command
        vehiculos, pesos = self._vehiculos()
        self.assertEqual(Command._eventos_de_hoy(random.Random(1), vehiculos, pesos, self._ahora_simulada(5, 30)), [])
        self.assertEqual(Command._eventos_de_hoy(random.Random(1), vehiculos, pesos, self._ahora_simulada(6, 10)), [])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SeedDemoResetTests(TestCase):

    def test_reset_recrea_solo_los_datos_de_demostracion(self):
        call_command('seed_demo', stdout=StringIO())
        propio = Propietario.objects.create(
            nombre='Persona Real', numero_identidad='0999999999', celular='0990000000',
            correo='real@unemi.edu.ec', tipo='Docente')
        vehiculo_propio = Vehiculo.objects.create(
            propietario=propio, placa='ZZZ-0001', marca='Kia', modelo='Rio', color='Gris')
        config = ConfiguracionQR.get_solo()
        config.expiration_days = 45
        config.save()
        usuarios = Usuario.objects.count()

        salida = StringIO()
        call_command('seed_demo', '--reset', stdout=salida)

        self.assertIn('Demo lista', salida.getvalue())
        self.assertEqual(Propietario.objects.count(), 16)       # 15 de demostración + el real
        self.assertEqual(Vehiculo.objects.count(), 21)
        self.assertTrue(Vehiculo.objects.filter(pk=vehiculo_propio.pk).exists())
        self.assertEqual(Usuario.objects.count(), usuarios)     # usuarios intactos
        self.assertEqual(ConfiguracionQR.get_solo().expiration_days, 45)   # configuración intacta
        self.assertGreater(RegistroMovimiento.objects.count(), 100)

    def test_reset_sin_datos_previos_tambien_funciona(self):
        call_command('seed_demo', '--reset', stdout=StringIO())
        self.assertEqual(Vehiculo.objects.count(), 20)

    def test_reset_deja_qr_de_demostracion_con_estados_esperados(self):
        call_command('seed_demo', '--reset', stdout=StringIO())
        call_command('seed_demo', '--reset', stdout=StringIO())
        ahora = timezone.now()
        self.assertEqual(CodigoQR.objects.count(), 20)
        self.assertEqual(CodigoQR.objects.filter(fecha_expiracion__lte=ahora).count(), 3)


class PeriodosEquivalentesTests(TestCase):
    """Semana y mes en curso se comparan contra el MISMO tramo del periodo anterior."""

    def _a_las(self, anio, mes, dia, hora=10):
        return timezone.make_aware(datetime(anio, mes, dia, hora, 0))

    def test_semana_en_curso_contra_los_mismos_dias_de_la_semana_pasada(self):
        from apps.qr.services.estadisticas import periodos_equivalentes
        ahora = self._a_las(2026, 11, 4)                       # miércoles 10:00
        desde, ant_desde, ant_hasta = periodos_equivalentes(ahora)['semana']
        self.assertEqual(desde, self._a_las(2026, 11, 2, 0))           # lunes
        self.assertEqual(ant_desde, self._a_las(2026, 10, 26, 0))      # lunes pasado
        self.assertEqual(ant_hasta, self._a_las(2026, 10, 28, 10))     # miércoles pasado 10:00

    def test_mes_en_curso_contra_los_mismos_dias_del_mes_pasado(self):
        from apps.qr.services.estadisticas import periodos_equivalentes
        ahora = self._a_las(2026, 11, 1, 3)                    # 1 de noviembre, 03:00
        desde, ant_desde, ant_hasta = periodos_equivalentes(ahora)['mes']
        self.assertEqual(desde, self._a_las(2026, 11, 1, 0))
        self.assertEqual(ant_desde, self._a_las(2026, 10, 1, 0))
        self.assertEqual(ant_hasta, self._a_las(2026, 10, 1, 3))       # solo 3 horas, no octubre entero

    def test_mes_pasado_mas_corto_no_se_sale_de_su_mes(self):
        from apps.qr.services.estadisticas import periodos_equivalentes
        ahora = self._a_las(2026, 3, 31)                       # febrero tiene 28 días
        desde, ant_desde, ant_hasta = periodos_equivalentes(ahora)['mes']
        self.assertEqual(ant_desde, self._a_las(2026, 2, 1, 0))
        self.assertEqual(ant_hasta, self._a_las(2026, 3, 1, 0))        # tope: fin de febrero

    def test_el_conteo_compara_tramos_iguales_y_no_da_menos_100(self):
        from apps.qr.services.estadisticas import _comparativos_ingresos, _variacion_pct
        propietario = Propietario.objects.create(
            nombre='Ana Mora', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente')
        vehiculo = Vehiculo.objects.create(
            propietario=propietario, placa='GAA-1111', marca='Kia', modelo='Rio', color='Gris')

        def ingreso(momento):
            registro = HistorialIngreso.objects.create(vehiculo=vehiculo)
            HistorialIngreso.objects.filter(pk=registro.pk).update(fecha_ingreso=momento)

        # Octubre: 2 ingresos el día 1 (dentro del tramo) y 5 al final del mes (fuera del tramo)
        ingreso(self._a_las(2026, 10, 1, 1))
        ingreso(self._a_las(2026, 10, 1, 2))
        for dia in range(20, 25):
            ingreso(self._a_las(2026, 10, dia))
        ingreso(self._a_las(2026, 11, 1, 1))                   # noviembre: 1 ingreso

        datos = _comparativos_ingresos(self._a_las(2026, 11, 1, 3))
        self.assertEqual(datos['ingresos_mes_actual'], 1)
        self.assertEqual(datos['ingresos_mes_pasado'], 2)      # solo el 1 de octubre hasta las 03:00
        self.assertEqual(_variacion_pct(datos['ingresos_mes_actual'], datos['ingresos_mes_pasado']), -50.0)


class SeedDemoAvisoTests(TestCase):
    def _a_las(self, hora, minuto=0):
        return timezone.make_aware(datetime.combine(timezone.localdate(), dtime(hora, minuto)))

    def test_jornada_sin_abrir_antes_de_las_0615(self):
        from apps.qr.management.commands.seed_demo import jornada_sin_abrir
        self.assertTrue(jornada_sin_abrir(self._a_las(3, 19)))
        self.assertTrue(jornada_sin_abrir(self._a_las(6, 14)))
        self.assertFalse(jornada_sin_abrir(self._a_las(6, 15)))
        self.assertFalse(jornada_sin_abrir(self._a_las(15)))

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_la_terminal_explica_por_que_no_hay_movimientos_de_hoy(self):
        from unittest import mock
        madrugada = self._a_las(3, 19)
        salida = StringIO()
        with mock.patch('apps.qr.management.commands.seed_demo.timezone.localtime', return_value=madrugada):
            call_command('seed_demo', stdout=salida)
        texto = salida.getvalue()
        self.assertIn('AVISO', texto)
        self.assertIn('03:19', texto)
        self.assertIn('seed_demo --reset', texto)
