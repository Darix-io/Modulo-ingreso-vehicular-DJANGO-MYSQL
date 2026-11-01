"""
Reportes del HISTORIAL de ingresos: filtros descritos, datos de los gráficos y
exportación a CSV, Excel y PDF.

Las tres exportaciones usan `filas_historial()`: solo cambia el formato de salida.
El PDF y el Excel llevan los colores de la marca GaritaQR (azul #0A2540 y ámbar #F59E0B).
"""
import csv
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..filters import parsear_entero, parsear_fecha

ENCABEZADOS = ['Fecha y hora', 'Placa', 'Marca', 'Modelo', 'Propietario', 'Tipo de propietario', 'Guardia']
# Marca y modelo van juntos en "Vehículo" para que todo quepa en una hoja
COLUMNAS_PDF = ['Fecha y hora', 'Placa', 'Vehículo', 'Propietario', 'Tipo de propietario', 'Guardia']
SIN_GUARDIA = 'Sin guardia'
MAXIMO_DIAS_GRAFICO = 366        # más días que esto no se rellenan los días sin ingresos

# Colores de la marca
AZUL = '#0A2540'
AMBAR = '#F59E0B'
FONDO = '#F5F7FB'
LINEA = '#E2E8F0'


# ------------------------------------------------------------------ utilidades
def nombre_guardia(usuario):
    """Nombre completo, o el usuario si no tiene; 'Sin guardia' si el usuario fue eliminado."""
    if usuario is None:
        return SIN_GUARDIA
    return usuario.get_full_name() or usuario.username


def guardias_con_ingresos():
    """Usuarios que han registrado al menos un ingreso (para el selector de guardia)."""
    return (
        get_user_model().objects.filter(historialingreso__isnull=False)
        .distinct().order_by('first_name', 'last_name', 'username')
    )


def descripcion_filtros(params):
    """Texto de los filtros aplicados, para el encabezado del PDF. 'Sin filtros' si no hay ninguno."""
    partes = []
    if params.get('q', '').strip():
        partes.append(f'Texto: «{params["q"].strip()}»')
    if params.get('placa', '').strip():
        partes.append(f'Placa: {params["placa"].strip().upper()}')
    guardia_id = parsear_entero(params.get('validador', '').strip())
    if guardia_id is not None:
        guardia = get_user_model().objects.filter(pk=guardia_id).first()
        partes.append(f'Guardia: {nombre_guardia(guardia) if guardia else "desconocido"}')
    inicio = parsear_fecha(params.get('fecha_inicio', '').strip())
    final = parsear_fecha(params.get('fecha_final', '').strip())
    if inicio:
        partes.append(f'Desde: {inicio:%d/%m/%Y}')
    if final:
        partes.append(f'Hasta: {final:%d/%m/%Y}')
    return ' · '.join(partes) if partes else 'Sin filtros (todos los ingresos)'


def _nombre_archivo(extension):
    return f"historial_ingresos_{timezone.localtime():%Y%m%d_%H%M%S}.{extension}"


def _respuesta_descarga(content_type, extension):
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{_nombre_archivo(extension)}"'
    return response


def _texto_seguro_csv(valor):
    """Evita 'inyección de fórmulas' cuando el CSV se abre en Excel."""
    texto = '' if valor is None else str(valor)
    if texto and texto[0] in ('=', '+', '-', '@'):
        return f"'{texto}"
    return texto


def filas_historial(queryset):
    """Convierte cada registro en una lista de textos lista para exportar."""
    for entrada in queryset.select_related('vehiculo__propietario', 'usuario_validador'):
        vehiculo = entrada.vehiculo
        yield [
            timezone.localtime(entrada.fecha_ingreso).strftime('%d/%m/%Y %H:%M:%S'),
            vehiculo.placa,
            vehiculo.marca,
            vehiculo.modelo,
            vehiculo.propietario.nombre,
            vehiculo.propietario.tipo,
            nombre_guardia(entrada.usuario_validador),
        ]


# ------------------------------------------------------------------ CSV y Excel
def exportar_csv(queryset):
    response = _respuesta_descarga('text/csv; charset=utf-8', 'csv')
    response.write('﻿')   # BOM: para que Excel muestre bien las tildes
    writer = csv.writer(response)
    writer.writerow(ENCABEZADOS)
    for fila in filas_historial(queryset):
        writer.writerow([_texto_seguro_csv(valor) for valor in fila])
    return response


def exportar_excel(queryset):
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Historial de ingresos'
    hoja.append(ENCABEZADOS)
    relleno = PatternFill('solid', start_color=AZUL.lstrip('#'))
    for celda in hoja[1]:
        celda.font = Font(bold=True, color='FFFFFF')
        celda.fill = relleno
        celda.alignment = Alignment(vertical='center')
    hoja.row_dimensions[1].height = 22
    for fila in filas_historial(queryset):
        hoja.append([_texto_seguro_csv(valor) for valor in fila])
    for letra, ancho in zip('ABCDEFG', (21, 12, 14, 16, 34, 20, 26)):
        hoja.column_dimensions[letra].width = ancho
    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = hoja.dimensions

    response = _respuesta_descarga(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx',
    )
    libro.save(response)
    return response


# ------------------------------------------------------------------ PDF
def _dibujar_logo(lienzo, x, y, lado):
    """El mismo logo de static/img/favicon.svg (viewBox 64x64), dibujado con reportlab."""
    lienzo.saveState()
    lienzo.translate(x, y + lado)
    lienzo.scale(lado / 64, -lado / 64)          # el SVG tiene el eje Y hacia abajo
    lienzo.setFillColor(colors.HexColor(AMBAR))
    lienzo.roundRect(0, 0, 64, 64, 14, stroke=0, fill=1)

    lienzo.setStrokeColor(colors.HexColor(AZUL))
    lienzo.setLineWidth(5)
    lienzo.setLineJoin(1)
    marco = lienzo.beginPath()
    for puntos in (((12, 24), (12, 12), (24, 12)), ((40, 12), (52, 12), (52, 24)),
                   ((52, 40), (52, 52), (40, 52)), ((24, 52), (12, 52), (12, 40))):
        marco.moveTo(*puntos[0])
        marco.lineTo(*puntos[1])
        marco.lineTo(*puntos[2])
    lienzo.drawPath(marco, stroke=1, fill=0)

    lienzo.setFillColor(colors.HexColor(AZUL))
    for x0, y0, ancho in ((22, 22, 8), (34, 22, 8), (22, 34, 8), (34, 34, 4), (38, 38, 4)):
        lienzo.rect(x0, y0, ancho, ancho, stroke=0, fill=1)
    lienzo.restoreState()


def _encabezado_y_pie(lienzo, documento):
    """Banda azul con el logo arriba y número de página abajo, en todas las hojas."""
    ancho, alto = documento.pagesize
    lienzo.saveState()

    banda = 2.1 * cm
    lienzo.setFillColor(colors.HexColor(AZUL))
    lienzo.rect(0, alto - banda, ancho, banda, stroke=0, fill=1)
    lienzo.setFillColor(colors.HexColor(AMBAR))
    lienzo.rect(0, alto - banda - 2.5, ancho, 2.5, stroke=0, fill=1)

    lado = 1.25 * cm
    _dibujar_logo(lienzo, documento.leftMargin, alto - banda + (banda - lado) / 2, lado)
    texto_x = documento.leftMargin + lado + 0.35 * cm
    lienzo.setFillColor(colors.white)
    lienzo.setFont('Helvetica-Bold', 17)
    lienzo.drawString(texto_x, alto - 1.12 * cm, 'Garita')
    ancho_garita = lienzo.stringWidth('Garita', 'Helvetica-Bold', 17)
    lienzo.setFillColor(colors.HexColor(AMBAR))
    lienzo.drawString(texto_x + ancho_garita, alto - 1.12 * cm, 'QR')
    lienzo.setFillColor(colors.HexColor('#C7D2E0'))
    lienzo.setFont('Helvetica', 8)
    lienzo.drawString(texto_x, alto - 1.62 * cm, 'UNEMI · Control de ingreso vehicular')
    lienzo.setFont('Helvetica', 9)
    lienzo.drawRightString(ancho - documento.rightMargin, alto - 1.3 * cm, 'Reporte de historial de ingresos')

    lienzo.setStrokeColor(colors.HexColor(LINEA))
    lienzo.line(documento.leftMargin, 1.35 * cm, ancho - documento.rightMargin, 1.35 * cm)
    lienzo.setFillColor(colors.HexColor('#64748B'))
    lienzo.setFont('Helvetica', 8)
    lienzo.drawString(documento.leftMargin, 0.9 * cm, 'GaritaQR · UNEMI')
    lienzo.drawRightString(ancho - documento.rightMargin, 0.9 * cm, f'Página {documento.page}')
    lienzo.restoreState()


def exportar_pdf(queryset, filtros='', usuario=None):
    response = _respuesta_descarga('application/pdf', 'pdf')
    documento = SimpleDocTemplate(
        response, pagesize=landscape(letter), title='Historial de ingresos · GaritaQR', author='GaritaQR UNEMI',
        leftMargin=1.3 * cm, rightMargin=1.3 * cm, topMargin=3.1 * cm, bottomMargin=1.9 * cm,
    )
    base = ParagraphStyle('base', fontName='Helvetica', fontSize=8.5, leading=11, alignment=TA_LEFT)
    titulo = ParagraphStyle('titulo', parent=base, fontName='Helvetica-Bold', fontSize=18, leading=22,
                            textColor=colors.HexColor(AZUL))
    meta = ParagraphStyle('meta', parent=base, fontSize=9, leading=13, textColor=colors.HexColor('#475569'))
    encabezado = ParagraphStyle('encabezado', parent=base, fontName='Helvetica-Bold', textColor=colors.white)

    filas = list(filas_historial(queryset))
    generado = f'{timezone.localtime():%d/%m/%Y %H:%M}'
    if usuario is not None:
        generado += f' por {nombre_guardia(usuario)}'

    datos = [[Paragraph(texto, encabezado) for texto in COLUMNAS_PDF]]
    for fecha, placa, marca, modelo, propietario, tipo, guardia in filas:
        datos.append([
            fecha, Paragraph(f'<b>{placa}</b>', base), Paragraph(f'{marca} {modelo}', base),
            Paragraph(propietario, base), tipo, Paragraph(guardia, base),
        ])
    anchos = [3.4 * cm, 2.5 * cm, 5.0 * cm, 6.3 * cm, 3.9 * cm, 3.6 * cm]
    tabla = Table(datos, colWidths=anchos, repeatRows=1, hAlign='LEFT')
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AZUL)),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(AMBAR)),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 1), (-1, -1), 0.4, colors.HexColor(LINEA)),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(FONDO)]),
    ]
    tabla.setStyle(TableStyle(estilo))

    contenido = [
        Paragraph('Historial de ingresos', titulo),
        Spacer(1, 4),
        Paragraph(f'<b>Generado:</b> {generado}', meta),
        Paragraph(f'<b>Filtros:</b> {filtros or "Sin filtros (todos los ingresos)"}', meta),
        Paragraph(f'<b>Total de registros:</b> {len(filas)}', meta),
        Spacer(1, 10),
    ]
    if filas:
        contenido.append(tabla)
    else:
        contenido.append(Paragraph('No hay ingresos con los filtros seleccionados.', meta))
    documento.build(contenido, onFirstPage=_encabezado_y_pie, onLaterPages=_encabezado_y_pie)
    return response


# ------------------------------------------------------------------ gráficos
def _dias_continuos(conteo, inicio, final):
    """Un valor por día (0 si no hubo ingresos) para que el gráfico no una días lejanos."""
    dias = []
    dia = inicio
    while dia <= final:
        dias.append(dia)
        dia += timedelta(days=1)
    return dias, [conteo.get(dia, 0) for dia in dias]


def datos_graficos(queryset, params=None):
    """
    Datos de los gráficos del reporte: ingresos por día e ingresos por guardia.
    Los días sin ingresos aparecen con 0 (rango: las fechas del filtro o, si no hay, del primer al último ingreso).
    """
    params = params or {}
    por_dia = (
        queryset.order_by().annotate(dia=TruncDate('fecha_ingreso'))
        .values('dia').annotate(total=Count('pk')).order_by('dia')
    )
    conteo = {fila['dia']: fila['total'] for fila in por_dia}

    dias, totales = [], []
    if conteo:
        inicio = parsear_fecha(params.get('fecha_inicio', '').strip()) or min(conteo)
        final = parsear_fecha(params.get('fecha_final', '').strip()) or max(conteo)
        if inicio <= final and (final - inicio).days < MAXIMO_DIAS_GRAFICO:
            dias, totales = _dias_continuos(conteo, inicio, final)
        else:
            dias, totales = sorted(conteo), [conteo[dia] for dia in sorted(conteo)]

    por_guardia = (
        queryset.order_by()
        .values('usuario_validador', 'usuario_validador__first_name',
                'usuario_validador__last_name', 'usuario_validador__username')
        .annotate(total=Count('pk')).order_by('-total')
    )
    etiquetas_guardia = []
    for fila in por_guardia:
        nombre = ' '.join(filter(None, (fila['usuario_validador__first_name'], fila['usuario_validador__last_name'])))
        etiquetas_guardia.append(nombre or fila['usuario_validador__username'] or SIN_GUARDIA)

    return {
        'labels': [dia.strftime('%d/%m') for dia in dias],
        'totals': totales,
        'labels_validador': etiquetas_guardia,
        'totals_validador': [fila['total'] for fila in por_guardia],
        'total': sum(conteo.values()),
    }
