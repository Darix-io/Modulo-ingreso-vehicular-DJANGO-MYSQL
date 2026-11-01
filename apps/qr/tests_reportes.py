"""Pruebas de la Fase 7: reportes (gráficos y descargas PDF, Excel y CSV)."""
import csv
import io
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from apps.qr.filters import filtrar_historial
from apps.qr.models import HistorialIngreso
from apps.qr.services import reportes

from .tests_base import BaseRegistrosTests, inicio_de_hoy


class DatosGraficosTests(BaseRegistrosTests):
    def test_rellena_con_cero_los_dias_sin_ingresos(self):
        base = inicio_de_hoy()
        self.ingreso(self.hilux, base - timedelta(days=3) + timedelta(hours=8))
        self.ingreso(self.sail, base - timedelta(days=3) + timedelta(hours=9))
        self.ingreso(self.hilux, base - timedelta(days=1) + timedelta(hours=8))
        datos = reportes.datos_graficos(HistorialIngreso.objects.all())
        self.assertEqual(datos['totals'], [2, 0, 1])
        self.assertEqual(len(datos['labels']), 3)
        self.assertEqual(datos['total'], 3)

    def test_el_rango_del_filtro_define_los_extremos_del_grafico(self):
        base = inicio_de_hoy()
        self.ingreso(self.hilux, base - timedelta(days=1) + timedelta(hours=8))
        hoy = timezone.localdate()
        params = {'fecha_inicio': (hoy - timedelta(days=3)).isoformat(), 'fecha_final': hoy.isoformat()}
        datos = reportes.datos_graficos(filtrar_historial(params), params)
        self.assertEqual(datos['totals'], [0, 0, 1, 0])

    def test_por_guardia_con_nombre_completo_y_sin_guardia(self):
        base = inicio_de_hoy() + timedelta(hours=7)
        for _ in range(3):
            self.ingreso(self.hilux, base, self.victor)
        self.ingreso(self.sail, base, self.luis)
        huerfano = self.ingreso(self.sail, base, self.luis)
        HistorialIngreso.objects.filter(pk=huerfano.pk).update(usuario_validador=None)
        datos = reportes.datos_graficos(HistorialIngreso.objects.all())
        self.assertEqual(datos['labels_validador'][0], 'Víctor Morán')       # el que más ingresos registró va primero
        self.assertEqual(dict(zip(datos['labels_validador'], datos['totals_validador'])),
                         {'Víctor Morán': 3, 'Luis Castro': 1, 'Sin guardia': 1})

    def test_sin_ingresos_devuelve_listas_vacias(self):
        datos = reportes.datos_graficos(HistorialIngreso.objects.all())
        self.assertEqual((datos['labels'], datos['totals'], datos['total']), ([], [], 0))


class PantallaReportesTests(BaseRegistrosTests):
    def setUp(self):
        self.ingreso(self.hilux, timezone.now() - timedelta(days=1), self.victor)
        self.ingreso(self.sail, timezone.now() - timedelta(hours=2), self.luis)

    def test_requiere_iniciar_sesion(self):
        for nombre in ('qr:reporte_historial', 'qr:reporte_historial_datos', 'qr:reporte_historial_pdf',
                       'qr:reporte_historial_excel', 'qr:reporte_historial_csv'):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 302, nombre)

    def test_pantalla_con_graficos_filtros_tabla_y_botones(self):
        self.client.force_login(self.victor)
        respuesta = self.client.get(reverse('qr:reporte_historial'), {'placa': 'GSA'})
        self.assertEqual(respuesta.status_code, 200)
        for texto in ('Ingresos por día', 'Ingresos por guardia', 'id="grafico-dias"', 'id="grafico-guardias"',
                      'chart.js@4.4.7', 'Aplicar filtros', 'Resultados', 'GSA-3841'):
            self.assertContains(respuesta, texto)
        self.assertNotContains(respuesta, 'PBA-7219')
        # el gráfico pide los datos con los mismos filtros
        self.assertEqual(respuesta.context['chart_data_url'], reverse('qr:reporte_historial_datos') + '?placa=GSA')
        for url in ('pdf_url', 'excel_url', 'csv_url'):
            self.assertIn('?placa=GSA', respuesta.context[url])
        for formato in ('pdf', 'xlsx', 'csv'):
            self.assertContains(respuesta, f'href="/qr/reportes/historial/{formato}/?placa=GSA"')

    def test_endpoint_de_datos_respeta_los_filtros(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:reporte_historial_datos'), {'validador': self.luis.pk})
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(datos['total'], 1)
        self.assertEqual(datos['labels_validador'], ['Luis Castro'])
        self.assertEqual(sum(datos['totals']), 1)


class DescargasTests(BaseRegistrosTests):
    def setUp(self):
        base = inicio_de_hoy()
        self.ingreso(self.hilux, base - timedelta(days=2) + timedelta(hours=8), self.victor)
        self.ingreso(self.sail, base - timedelta(days=1) + timedelta(hours=9), self.luis)
        self.ingreso(self.sail, base + timedelta(hours=7), self.luis)
        self.client.force_login(self.victor)

    def filas_csv(self, **params):
        respuesta = self.client.get(reverse('qr:reporte_historial_csv'), params)
        self.assertEqual(respuesta.status_code, 200)
        texto = respuesta.content.decode('utf-8-sig')
        return respuesta, list(csv.reader(io.StringIO(texto)))

    def test_csv_con_encabezados_y_nombres_de_guardia(self):
        respuesta, filas = self.filas_csv()
        self.assertTrue(respuesta['Content-Type'].startswith('text/csv'))
        self.assertIn('.csv', respuesta['Content-Disposition'])
        self.assertEqual(filas[0], ['Fecha y hora', 'Placa', 'Marca', 'Modelo', 'Propietario',
                                    'Tipo de propietario', 'Guardia'])
        self.assertEqual(len(filas) - 1, 3)
        self.assertIn(['Toyota', 'Hilux', 'Ana Mora Vera', 'Docente', 'Víctor Morán'], [fila[2:] for fila in filas])

    def test_csv_respeta_filtros_y_orden(self):
        _, filas = self.filas_csv(validador=self.luis.pk)
        self.assertEqual(len(filas) - 1, 2)
        self.assertTrue(all(fila[6] == 'Luis Castro' for fila in filas[1:]))
        _, ordenadas = self.filas_csv(orden='vehiculo__placa')
        self.assertEqual([fila[1] for fila in ordenadas[1:]], ['GSA-3841', 'PBA-7219', 'PBA-7219'])

    def test_csv_no_permite_inyeccion_de_formulas(self):
        self.ana.nombre = '=HYPERLINK("http://malo.example")'
        self.ana.save()
        _, filas = self.filas_csv(placa='GSA')
        self.assertEqual(filas[1][4], '\'=HYPERLINK("http://malo.example")')

    def test_excel_se_abre_con_el_estilo_de_la_marca(self):
        respuesta = self.client.get(reverse('qr:reporte_historial_excel'), {'validador': self.luis.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('spreadsheetml', respuesta['Content-Type'])
        self.assertIn('.xlsx', respuesta['Content-Disposition'])
        hoja = load_workbook(io.BytesIO(respuesta.content)).active
        self.assertEqual(hoja.max_row, 3)                                  # encabezado + 2 ingresos del filtro
        self.assertEqual(hoja['B2'].value, 'PBA-7219')
        self.assertEqual(hoja['A1'].value, 'Fecha y hora')
        self.assertTrue(hoja['A1'].font.bold)
        self.assertTrue(hoja['A1'].fill.start_color.rgb.endswith('0A2540'))
        self.assertEqual(hoja.freeze_panes, 'A2')

    def test_pdf_valido_con_marca_filtros_y_total(self):
        respuesta = self.client.get(reverse('qr:reporte_historial_pdf'), {'validador': self.luis.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertIn('.pdf', respuesta['Content-Disposition'])
        self.assertTrue(respuesta.content.startswith(b'%PDF'))
        self.assertIn(b'GaritaQR UNEMI', respuesta.content)                # autor del documento

    def test_pdf_sin_resultados_no_falla(self):
        respuesta = self.client.get(reverse('qr:reporte_historial_pdf'), {'placa': 'ZZZ'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.content.startswith(b'%PDF'))

    def test_pdf_con_muchos_registros_ocupa_varias_hojas(self):
        base = inicio_de_hoy() + timedelta(hours=1)
        HistorialIngreso.objects.bulk_create(
            [HistorialIngreso(vehiculo=self.hilux, usuario_validador=self.victor) for _ in range(120)])
        HistorialIngreso.objects.update(fecha_ingreso=base)
        respuesta = self.client.get(reverse('qr:reporte_historial_pdf'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertGreater(respuesta.content.count(b'/Type /Page\n'), 1)

    def test_descripcion_de_filtros_del_pdf(self):
        self.assertEqual(reportes.descripcion_filtros({}), 'Sin filtros (todos los ingresos)')
        texto = reportes.descripcion_filtros({
            'q': 'hilux', 'placa': 'gsa', 'validador': str(self.luis.pk),
            'fecha_inicio': '2026-10-01', 'fecha_final': '2026-10-31'})
        for parte in ('Texto: «hilux»', 'Placa: GSA', 'Guardia: Luis Castro', 'Desde: 01/10/2026', 'Hasta: 31/10/2026'):
            self.assertIn(parte, texto)
