"""Pruebas de la Fase 7: pantalla de Movimientos (contadores de hoy y filtros)."""
from datetime import timedelta

from django.urls import reverse

from apps.qr.filters import filtrar_movimientos, leer_filtros_movimientos
from apps.qr.models import RegistroMovimiento
from apps.qr.services.movimientos import contadores_hoy

from .tests_base import BaseRegistrosTests, inicio_de_hoy


class ContadoresMovimientosTests(BaseRegistrosTests):
    def test_cuenta_solo_hoy_y_separa_ingresos_y_salidas_autorizados(self):
        hoy = inicio_de_hoy() + timedelta(minutes=1)
        ayer = inicio_de_hoy() - timedelta(hours=1)
        A, D = RegistroMovimiento.AUTORIZADO, RegistroMovimiento.DENEGADO
        self.movimiento(self.hilux, A, RegistroMovimiento.INGRESO, fecha=hoy)
        self.movimiento(self.hilux, A, RegistroMovimiento.SALIDA, fecha=hoy)
        self.movimiento(self.sail, A, RegistroMovimiento.INGRESO, fecha=hoy)
        self.movimiento(self.sail, D, RegistroMovimiento.INGRESO, 'Código expirado', fecha=hoy)   # no es un ingreso real
        self.movimiento(self.sail, A, RegistroMovimiento.INGRESO, fecha=ayer)                      # ayer: no cuenta
        cuentas = contadores_hoy(ahora=hoy + timedelta(hours=1))
        self.assertEqual(cuentas['total'], 4)
        self.assertEqual(cuentas['autorizados'], 3)
        self.assertEqual(cuentas['denegados'], 1)
        self.assertEqual(cuentas['ingresos'], 2)
        self.assertEqual(cuentas['salidas'], 1)
        self.assertEqual(cuentas['pct_autorizados'], 75.0)
        self.assertEqual(cuentas['pct_denegados'], 25.0)

    def test_sin_movimientos_no_inventa_porcentajes(self):
        cuentas = contadores_hoy()
        self.assertEqual((cuentas['total'], cuentas['autorizados'], cuentas['denegados']), (0, 0, 0))
        self.assertIsNone(cuentas['pct_autorizados'])
        self.assertIsNone(cuentas['pct_denegados'])


class FiltrosMovimientosTests(BaseRegistrosTests):
    def setUp(self):
        A, D = RegistroMovimiento.AUTORIZADO, RegistroMovimiento.DENEGADO
        self.m1 = self.movimiento(self.hilux, A, RegistroMovimiento.INGRESO)
        self.m2 = self.movimiento(self.hilux, A, RegistroMovimiento.SALIDA)
        self.m3 = self.movimiento(self.sail, D, RegistroMovimiento.INGRESO, 'Vehículo suspendido')

    def filtrar(self, **params):
        return set(filtrar_movimientos(leer_filtros_movimientos(params)))

    def test_por_placa_parcial_sin_importar_mayusculas(self):
        self.assertEqual(self.filtrar(placa='gsa'), {self.m1, self.m2})
        self.assertEqual(self.filtrar(placa='7219'), {self.m3})

    def test_por_tipo_y_estado(self):
        self.assertEqual(self.filtrar(tipo='salida'), {self.m2})
        self.assertEqual(self.filtrar(estado='denegado'), {self.m3})
        self.assertEqual(self.filtrar(estado='autorizado', tipo='ingreso'), {self.m1})

    def test_valores_desconocidos_se_ignoran(self):
        self.assertEqual(self.filtrar(tipo='xyz', estado='???'), {self.m1, self.m2, self.m3})


class PantallaMovimientosTests(BaseRegistrosTests):
    def test_requiere_iniciar_sesion(self):
        self.assertEqual(self.client.get(reverse('qr:movimientos')).status_code, 302)

    def test_muestra_contadores_motivo_real_y_guardia(self):
        hoy = inicio_de_hoy() + timedelta(minutes=5)
        self.movimiento(self.hilux, RegistroMovimiento.AUTORIZADO, detalle='Acceso autorizado', fecha=hoy)
        self.movimiento(self.sail, RegistroMovimiento.DENEGADO, detalle='Vehículo suspendido', guardia=self.luis, fecha=hoy)
        for usuario in (self.admin, self.victor):
            self.client.force_login(usuario)
            respuesta = self.client.get(reverse('qr:movimientos'))
            self.assertEqual(respuesta.status_code, 200)
            self.assertEqual(respuesta.context['contadores']['total'], 2)
            for texto in ('Total de hoy', 'Autorizados', 'Denegados', 'Ingresos y salidas',
                          'Vehículo suspendido', 'Acceso autorizado', 'Luis Castro', 'Víctor Morán',
                          'Ana Mora Vera', 'GSA-3841', 'Motivo o detalle'):
                self.assertContains(respuesta, texto)

    def test_filtra_por_placa_tipo_y_estado_desde_la_pantalla(self):
        self.movimiento(self.hilux, RegistroMovimiento.AUTORIZADO)
        self.movimiento(self.sail, RegistroMovimiento.DENEGADO, detalle='Código expirado')
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:movimientos'), {'estado': 'denegado'})
        self.assertContains(respuesta, 'Código expirado')
        self.assertNotContains(respuesta, 'Ana Mora Vera')
        respuesta = self.client.get(reverse('qr:movimientos'), {'placa': 'gsa-38'})
        self.assertContains(respuesta, 'Ana Mora Vera')
        self.assertNotContains(respuesta, 'Pedro Loor Zambrano')

    def test_los_contadores_de_hoy_no_cambian_con_los_filtros(self):
        self.movimiento(self.hilux, RegistroMovimiento.AUTORIZADO, fecha=inicio_de_hoy() + timedelta(minutes=1))
        self.movimiento(self.sail, RegistroMovimiento.DENEGADO, detalle='x', fecha=inicio_de_hoy() + timedelta(minutes=2))
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:movimientos'), {'estado': 'denegado'})
        self.assertEqual(respuesta.context['contadores']['total'], 2)
        self.assertEqual(len(respuesta.context['movimientos']), 1)

    def test_la_paginacion_conserva_los_filtros(self):
        for _ in range(20):
            self.movimiento(self.sail, RegistroMovimiento.DENEGADO, detalle='Código expirado')
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:movimientos'), {'estado': 'denegado'})
        self.assertContains(respuesta, 'page=2')
        self.assertContains(respuesta, 'estado=denegado')
        self.assertEqual(len(respuesta.context['movimientos']), 15)

    def test_estado_vacio_distingue_filtros_de_no_hay_datos(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('qr:movimientos')), 'Todavía no hay movimientos registrados')
        self.assertContains(self.client.get(reverse('qr:movimientos'), {'placa': 'ZZZ'}), 'No hay movimientos con esos filtros')

    def test_el_enlace_desde_el_detalle_del_qr_filtra_por_placa(self):
        self.movimiento(self.hilux, RegistroMovimiento.AUTORIZADO)
        self.movimiento(self.sail, RegistroMovimiento.AUTORIZADO)
        self.client.force_login(self.admin)
        detalle = self.client.get(reverse('qr:detalle', args=[self.hilux.codigo_qr.pk]))
        self.assertContains(detalle, reverse('qr:movimientos') + '?placa=GSA-3841')
        respuesta = self.client.get(reverse('qr:movimientos'), {'placa': 'GSA-3841'})
        self.assertNotContains(respuesta, 'PBA-7219')
