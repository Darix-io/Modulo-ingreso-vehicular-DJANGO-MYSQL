"""Pruebas de la Fase 7: historial de ingresos (filtros, orden y total)."""
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.qr.filters import filtrar_historial, rango_invalido, rangos_rapidos
from apps.qr.models import HistorialIngreso, RegistroMovimiento
from apps.qr.services import reportes

from .tests_base import BaseRegistrosTests, inicio_de_hoy


class FiltrosHistorialTests(BaseRegistrosTests):
    def setUp(self):
        base = inicio_de_hoy()
        self.h1 = self.ingreso(self.hilux, base - timedelta(days=5, hours=-9), self.victor)
        self.h2 = self.ingreso(self.sail, base - timedelta(days=2, hours=-10), self.luis)
        self.h3 = self.ingreso(self.hilux, base + timedelta(hours=8), self.luis)

    def filtrar(self, **params):
        return set(filtrar_historial(params))

    def test_texto_busca_en_placa_vehiculo_propietario_cedula_y_guardia(self):
        self.assertEqual(self.filtrar(q='hilux'), {self.h1, self.h3})
        self.assertEqual(self.filtrar(q='Pedro Loor'), {self.h2})
        self.assertEqual(self.filtrar(q='0912345678'), {self.h1, self.h3})
        self.assertEqual(self.filtrar(q='Castro'), {self.h2, self.h3})

    def test_placa_parcial(self):
        self.assertEqual(self.filtrar(placa='pba'), {self.h2})

    def test_guardia_se_filtra_por_id_exacto(self):
        # 'seguridad' está contenido en 'seguridad2': por id no se confunden
        self.assertEqual(self.filtrar(validador=str(self.victor.pk)), {self.h1})
        self.assertEqual(self.filtrar(validador=str(self.luis.pk)), {self.h2, self.h3})
        self.assertEqual(self.filtrar(validador='no-es-un-numero'), {self.h1, self.h2, self.h3})

    def test_rango_de_fechas_incluye_los_dos_extremos(self):
        hoy = timezone.localdate()
        self.assertEqual(self.filtrar(fecha_inicio=hoy.isoformat()), {self.h3})
        self.assertEqual(self.filtrar(fecha_final=(hoy - timedelta(days=2)).isoformat()), {self.h1, self.h2})
        self.assertEqual(self.filtrar(fecha_inicio=(hoy - timedelta(days=2)).isoformat(),
                                      fecha_final=hoy.isoformat()), {self.h2, self.h3})
        self.assertEqual(self.filtrar(fecha_inicio='basura'), {self.h1, self.h2, self.h3})

    def test_rango_invalido_y_atajos(self):
        self.assertTrue(rango_invalido({'fecha_inicio': '2026-10-10', 'fecha_final': '2026-10-01'}))
        self.assertFalse(rango_invalido({'fecha_inicio': '2026-10-01', 'fecha_final': '2026-10-10'}))
        self.assertFalse(rango_invalido({'fecha_inicio': '2026-10-01'}))
        atajos = rangos_rapidos(hoy=timezone.localdate().replace(year=2026, month=11, day=15))
        self.assertEqual(atajos[0], ('Hoy', '2026-11-15', '2026-11-15'))
        self.assertEqual(atajos[1], ('Últimos 7 días', '2026-11-09', '2026-11-15'))
        self.assertEqual(atajos[2], ('Este mes', '2026-11-01', '2026-11-15'))

    def test_solo_hay_guardias_que_registraron_ingresos(self):
        self.assertEqual(set(reportes.guardias_con_ingresos()), {self.victor, self.luis})
        HistorialIngreso.objects.filter(usuario_validador=self.victor).delete()
        self.assertEqual(set(reportes.guardias_con_ingresos()), {self.luis})


class PantallaHistorialTests(BaseRegistrosTests):
    def setUp(self):
        self.ingreso(self.hilux, timezone.now() - timedelta(days=1), self.victor)
        self.ingreso(self.sail, timezone.now() - timedelta(hours=3), self.luis)
        # un intento denegado: NO debe aparecer en el historial
        self.movimiento(self.sail, RegistroMovimiento.DENEGADO, detalle='Código expirado')

    def test_requiere_iniciar_sesion(self):
        self.assertEqual(self.client.get(reverse('qr:historial')).status_code, 302)

    def test_solo_ingresos_autorizados_con_total_y_sin_columna_de_estado(self):
        for usuario in (self.admin, self.victor):
            self.client.force_login(usuario)
            respuesta = self.client.get(reverse('qr:historial'))
            self.assertEqual(respuesta.status_code, 200)
            self.assertEqual(respuesta.context['total_registros'], 2)
            for texto in ('Total de ingresos', 'GSA-3841', 'Ana Mora Vera', 'Víctor Morán', 'Luis Castro',
                          'Todos los guardias', 'Hoy', 'Últimos 7 días', 'Este mes'):
                self.assertContains(respuesta, texto)
            self.assertNotContains(respuesta, 'Código expirado')
            self.assertNotContains(respuesta, 'Denegado')
            self.assertNotContains(respuesta, '>Estado<')

    def test_filtra_por_guardia_y_muestra_el_total_filtrado(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:historial'), {'validador': self.luis.pk})
        self.assertEqual(respuesta.context['total_registros'], 1)
        self.assertContains(respuesta, 'con los filtros aplicados')
        self.assertContains(respuesta, f'<option value="{self.luis.pk}" selected>')

    def test_columnas_ordenables_y_orden_seguro(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:historial'), {'orden': 'vehiculo__placa'})
        placas = [h.vehiculo.placa for h in respuesta.context['historial']]
        self.assertEqual(placas, ['GSA-3841', 'PBA-7219'])
        self.assertContains(respuesta, 'orden=-vehiculo__placa')          # el siguiente clic ordena al revés
        # un campo no permitido se ignora (no da error)
        self.assertEqual(self.client.get(reverse('qr:historial'), {'orden': 'password'}).status_code, 200)

    def test_rango_invalido_avisa(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:historial'), {'fecha_inicio': '2026-10-10', 'fecha_final': '2026-10-01'})
        self.assertContains(respuesta, 'posterior a la final')

    def test_enlace_a_reportes_conserva_los_filtros(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:historial'), {'placa': 'GSA'})
        self.assertContains(respuesta, reverse('qr:reporte_historial') + '?placa=GSA')

    def test_estado_vacio(self):
        HistorialIngreso.objects.all().delete()
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('qr:historial')), 'Todavía no hay ingresos registrados')
