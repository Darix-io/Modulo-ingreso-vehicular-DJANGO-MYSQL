"""
Exportación del historial de ingresos a CSV, Excel y PDF.

Antes las tres funciones repetían el mismo bucle para armar las filas.
Ahora todas usan `filas_historial()` y solo cambia el formato de salida.
"""
import csv

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ENCABEZADOS = ['Fecha de ingreso', 'Placa', 'Marca', 'Modelo', 'Validador']


def _nombre_archivo(extension):
    return f"historial_accesos_{timezone.now():%Y%m%d_%H%M%S}.{extension}"


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
    for entrada in queryset.select_related('vehiculo', 'usuario_validador'):
        validador = entrada.usuario_validador
        nombre_validador = (validador.get_full_name() or validador.username) if validador else 'Invitado'
        yield [
            timezone.localtime(entrada.fecha_ingreso).strftime('%Y-%m-%d %H:%M:%S'),
            entrada.vehiculo.placa,
            entrada.vehiculo.marca,
            entrada.vehiculo.modelo,
            nombre_validador,
        ]


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
    hoja.title = 'Historial Accesos'
    hoja.append(ENCABEZADOS)
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    for fila in filas_historial(queryset):
        hoja.append(fila)
    for columna in hoja.columns:
        hoja.column_dimensions[columna[0].column_letter].width = 22

    response = _respuesta_descarga(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx',
    )
    libro.save(response)
    return response


def exportar_pdf(queryset):
    response = _respuesta_descarga('application/pdf', 'pdf')
    documento = SimpleDocTemplate(response, pagesize=letter)
    estilos = getSampleStyleSheet()

    datos = [ENCABEZADOS] + list(filas_historial(queryset))
    tabla = Table(datos, repeatRows=1, hAlign='LEFT')
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))

    documento.build([
        Paragraph('Reporte de Historial de Accesos', estilos['Title']),
        Spacer(1, 12),
        Paragraph(f'Fecha de generación: {timezone.localtime():%Y-%m-%d %H:%M:%S}', estilos['Normal']),
        Spacer(1, 12),
        tabla,
    ])
    return response


def datos_graficos(queryset):
    """Datos para los gráficos del reporte (por día y por validador)."""
    por_dia = (
        queryset.annotate(dia=TruncDate('fecha_ingreso'))
        .values('dia').annotate(total=Count('id')).order_by('dia')
    )
    por_validador = (
        queryset.values('usuario_validador__username')
        .annotate(total=Count('id')).order_by('-total')
    )
    return {
        'labels': [item['dia'].strftime('%d/%m/%Y') for item in por_dia],
        'totals': [item['total'] for item in por_dia],
        'labels_validador': [item['usuario_validador__username'] or 'Invitado' for item in por_validador],
        'totals_validador': [item['total'] for item in por_validador],
    }
