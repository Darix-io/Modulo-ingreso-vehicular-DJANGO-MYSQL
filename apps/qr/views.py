import csv
import os
from datetime import datetime

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from apps.usuarios.mixins import RoleRequiredMixin
from .forms import ConfiguracionQRForm
from .models import ConfiguracionQR, CodigoQR, HistorialIngreso, RegistroMovimiento

class QrListView(RoleRequiredMixin, ListView):
    role_required = 'Seguridad o Administrador'
    model = CodigoQR
    template_name = 'qr/qr_list.html'
    context_object_name = 'qrs'
    ordering = ['-fecha_creacion']
    paginate_by = 10


def safe_csv_value(value):
    text = str(value) if value is not None else ''
    if text and text[0] in ('=', '+', '-', '@'):
        return f"'{text}"
    return text


def filtrar_historial_ingresos(request, queryset=None):
    if queryset is None:
        queryset = HistorialIngreso.objects.select_related('vehiculo', 'usuario_validador')

    q = request.GET.get('q', '').strip()
    placa = request.GET.get('placa', '').strip()
    validador = request.GET.get('validador', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_final = request.GET.get('fecha_final', '').strip()

    if q:
        queryset = queryset.filter(
            Q(vehiculo__placa__icontains=q)
            | Q(vehiculo__marca__icontains=q)
            | Q(vehiculo__modelo__icontains=q)
            | Q(usuario_validador__username__icontains=q)
            | Q(usuario_validador__first_name__icontains=q)
            | Q(usuario_validador__last_name__icontains=q)
        )

    if placa:
        queryset = queryset.filter(vehiculo__placa__icontains=placa)

    if validador:
        queryset = queryset.filter(
            Q(usuario_validador__username__icontains=validador)
            | Q(usuario_validador__first_name__icontains=validador)
            | Q(usuario_validador__last_name__icontains=validador)
        )

    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            queryset = queryset.filter(fecha_ingreso__date__gte=fecha_inicio_dt)
        except ValueError:
            pass

    if fecha_final:
        try:
            fecha_final_dt = datetime.strptime(fecha_final, '%Y-%m-%d').date()
            queryset = queryset.filter(fecha_ingreso__date__lte=fecha_final_dt)
        except ValueError:
            pass

    return queryset


def query_string_without_page(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


class HistorialListView(RoleRequiredMixin, ListView):
    role_required = 'Seguridad o Administrador'
    model = HistorialIngreso
    template_name = 'qr/historial.html'
    context_object_name = 'historial'
    paginate_by = 10

    def get_queryset(self):
        queryset = filtrar_historial_ingresos(self.request)
        orden = self.request.GET.get('orden', '-fecha_ingreso')

        if orden not in [
            'fecha_ingreso',
            '-fecha_ingreso',
            'vehiculo__placa',
            '-vehiculo__placa',
            'usuario_validador__username',
            '-usuario_validador__username',
        ]:
            orden = '-fecha_ingreso'

        return queryset.order_by(orden)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        orden = request.GET.get('orden', '-fecha_ingreso')
        context.update({
            'search_query': request.GET.get('q', ''),
            'placa_filter': request.GET.get('placa', ''),
            'validador_filter': request.GET.get('validador', ''),
            'orden': orden,
            'orden_vehiculo': '-vehiculo__placa' if orden == 'vehiculo__placa' else 'vehiculo__placa',
            'orden_fecha': '-fecha_ingreso' if orden == 'fecha_ingreso' else 'fecha_ingreso',
            'orden_validador': '-usuario_validador__username' if orden == 'usuario_validador__username' else 'usuario_validador__username',
            'total_registros': self.get_queryset().count(),
        })
        return context


class HistorialReporteView(RoleRequiredMixin, ListView):
    role_required = 'Seguridad o Administrador'
    model = HistorialIngreso
    template_name = 'qr/reporte_historial.html'
    context_object_name = 'historial'
    paginate_by = 20

    def get_queryset(self):
        queryset = filtrar_historial_ingresos(self.request)
        orden = self.request.GET.get('orden', '-fecha_ingreso')

        if orden not in [
            'fecha_ingreso',
            '-fecha_ingreso',
            'vehiculo__placa',
            '-vehiculo__placa',
            'usuario_validador__username',
            '-usuario_validador__username',
        ]:
            orden = '-fecha_ingreso'

        return queryset.order_by(orden)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        orden = request.GET.get('orden', '-fecha_ingreso')
        query_string = query_string_without_page(request)
        csv_link = f"{request.path}csv/?{query_string}" if query_string else f"{request.path}csv/"
        excel_link = f"{request.path}xlsx/?{query_string}" if query_string else f"{request.path}xlsx/"
        pdf_link = f"{request.path}pdf/?{query_string}" if query_string else f"{request.path}pdf/"
        data_link = f"{request.path}datos/?{query_string}" if query_string else f"{request.path}datos/"

        context.update({
            'search_query': request.GET.get('q', ''),
            'placa_filter': request.GET.get('placa', ''),
            'validador_filter': request.GET.get('validador', ''),
            'fecha_inicio': request.GET.get('fecha_inicio', ''),
            'fecha_final': request.GET.get('fecha_final', ''),
            'orden': orden,
            'orden_vehiculo': '-vehiculo__placa' if orden == 'vehiculo__placa' else 'vehiculo__placa',
            'orden_fecha': '-fecha_ingreso' if orden == 'fecha_ingreso' else 'fecha_ingreso',
            'orden_validador': '-usuario_validador__username' if orden == 'usuario_validador__username' else 'usuario_validador__username',
            'total_registros': self.get_queryset().count(),
            'csv_url': csv_link,
            'excel_url': excel_link,
            'pdf_url': pdf_link,
            'chart_data_url': data_link,
        })
        return context


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_administrador() or u.is_personal_seguridad())
def exportar_historial_csv(request):
    queryset = filtrar_historial_ingresos(request).order_by('-fecha_ingreso')
    filename = f"historial_accesos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow([
        'Fecha de ingreso',
        'Placa',
        'Marca',
        'Modelo',
        'Validador',
    ])

    for entrada in queryset:
        validador = entrada.usuario_validador.get_full_name() if entrada.usuario_validador else 'Invitado'
        writer.writerow([
            safe_csv_value(entrada.fecha_ingreso.strftime('%Y-%m-%d %H:%M:%S')),
            safe_csv_value(entrada.vehiculo.placa),
            safe_csv_value(entrada.vehiculo.marca),
            safe_csv_value(entrada.vehiculo.modelo),
            safe_csv_value(validador),
        ])

    return response


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_administrador() or u.is_personal_seguridad())
def exportar_historial_excel(request):
    queryset = filtrar_historial_ingresos(request).order_by('-fecha_ingreso')
    filename = f"historial_accesos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Historial Accesos'

    headers = ['Fecha de ingreso', 'Placa', 'Marca', 'Modelo', 'Validador']
    worksheet.append(headers)

    for entrada in queryset:
        validador = entrada.usuario_validador.get_full_name() if entrada.usuario_validador else 'Invitado'
        worksheet.append([
            entrada.fecha_ingreso.strftime('%Y-%m-%d %H:%M:%S'),
            entrada.vehiculo.placa,
            entrada.vehiculo.marca,
            entrada.vehiculo.modelo,
            validador,
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_administrador() or u.is_personal_seguridad())
def exportar_historial_pdf(request):
    queryset = filtrar_historial_ingresos(request).order_by('-fecha_ingreso')
    filename = f"historial_accesos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Reporte de Historial de Accesos', styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f'Fecha de generación: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [['Fecha de ingreso', 'Placa', 'Marca', 'Modelo', 'Validador']]
    for entrada in queryset:
        validador = entrada.usuario_validador.get_full_name() if entrada.usuario_validador else 'Invitado'
        data.append([
            entrada.fecha_ingreso.strftime('%Y-%m-%d %H:%M:%S'),
            entrada.vehiculo.placa,
            entrada.vehiculo.marca,
            entrada.vehiculo.modelo,
            validador,
        ])

    table = Table(data, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))

    elements.append(table)
    doc.build(elements)
    return response


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_administrador() or u.is_personal_seguridad())
def datos_reporte_historial(request):
    queryset = filtrar_historial_ingresos(request)
    dia_data = list(
        queryset.annotate(dia=TruncDate('fecha_ingreso'))
        .values('dia')
        .annotate(total=Count('id'))
        .order_by('dia')
    )
    validador_data = list(
        queryset.values('usuario_validador__username')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    labels = [item['dia'].strftime('%d/%m/%Y') for item in dia_data]
    totals = [item['total'] for item in dia_data]
    labels_validador = [item['usuario_validador__username'] or 'Invitado' for item in validador_data]
    totals_validador = [item['total'] for item in validador_data]

    return JsonResponse({
        'labels': labels,
        'totals': totals,
        'labels_validador': labels_validador,
        'totals_validador': totals_validador,
    })

class RegistroMovimientoListView(RoleRequiredMixin, ListView):
    role_required = 'Seguridad o Administrador'
    model = RegistroMovimiento
    template_name = 'qr/movimientos.html'
    context_object_name = 'movimientos'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        vehiculo_placa = self.request.GET.get('vehiculo')
        if vehiculo_placa:
            queryset = queryset.filter(vehiculo__placa__iexact=vehiculo_placa)
        return queryset

class QrDetailView(RoleRequiredMixin, DetailView):
    role_required = 'Seguridad o Administrador'
    model = CodigoQR
    template_name = 'qr/qr_detail.html'
    context_object_name = 'qr'

class QrDownloadView(RoleRequiredMixin, View):
    role_required = 'Seguridad o Administrador'

    def get(self, request, pk, *args, **kwargs):
        codigo_qr = get_object_or_404(CodigoQR, pk=pk)
        if not codigo_qr.imagen or not codigo_qr.imagen.path:
            raise Http404("Imagen de QR no disponible")
        try:
            response = FileResponse(open(codigo_qr.imagen.path, 'rb'), as_attachment=True, filename=os.path.basename(codigo_qr.imagen.name))
            return response
        except FileNotFoundError:
            raise Http404("Archivo de QR no encontrado")

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_administrador() or u.is_personal_seguridad())
def renovar_qr_view(request, pk):
    codigo_qr = get_object_or_404(CodigoQR, pk=pk)
    codigo_qr.renovar()
    messages.success(request, 'Código QR renovado con éxito.')
    return redirect('qr:lista')


def validar_acceso_view(request):
    token = request.GET.get('token')
    resultado = None

    if token and 'token=' in token:
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(token)
            token = parse_qs(parsed.query).get('token', [token])[0]
        except Exception:
            pass

    if token:
        try:
            qr = CodigoQR.objects.get(contenido=token)
            ultimo_autorizado = qr.movimientos.filter(estado=RegistroMovimiento.AUTORIZADO).order_by('-fecha').first()
            tipo = RegistroMovimiento.INGRESO

            if ultimo_autorizado and ultimo_autorizado.tipo == RegistroMovimiento.INGRESO:
                tipo = RegistroMovimiento.SALIDA

            config = ConfiguracionQR.get_solo()

            if not config.activar_qr:
                RegistroMovimiento.objects.create(
                    codigo_qr=qr,
                    vehiculo=qr.vehiculo,
                    tipo=tipo,
                    estado=RegistroMovimiento.DENEGADO,
                    usuario_validador=request.user if request.user.is_authenticated else None,
                    detalle='Validación deshabilitada en la configuración'
                )
                resultado = {'status': 'danger', 'mensaje': 'Validación de QR deshabilitada'}
            elif not qr.activo:
                RegistroMovimiento.objects.create(
                    codigo_qr=qr,
                    vehiculo=qr.vehiculo,
                    tipo=tipo,
                    estado=RegistroMovimiento.DENEGADO,
                    usuario_validador=request.user if request.user.is_authenticated else None,
                    detalle='Código desactivado'
                )
                resultado = {'status': 'danger', 'mensaje': 'Código desactivado'}
            elif qr.is_expired:
                qr.activo = False
                qr.save(update_fields=['activo'])
                RegistroMovimiento.objects.create(
                    codigo_qr=qr,
                    vehiculo=qr.vehiculo,
                    tipo=tipo,
                    estado=RegistroMovimiento.DENEGADO,
                    usuario_validador=request.user if request.user.is_authenticated else None,
                    detalle='Código expirado'
                )
                resultado = {'status': 'danger', 'mensaje': 'Código expirado'}
            else:
                movimiento = RegistroMovimiento.objects.create(
                    codigo_qr=qr,
                    vehiculo=qr.vehiculo,
                    tipo=tipo,
                    estado=RegistroMovimiento.AUTORIZADO,
                    usuario_validador=request.user if request.user.is_authenticated else None,
                    detalle='Acceso autorizado' if tipo == RegistroMovimiento.INGRESO else 'Salida autorizada'
                )

                if tipo == RegistroMovimiento.INGRESO:
                    HistorialIngreso.objects.create(
                        vehiculo=qr.vehiculo,
                        usuario_validador=request.user if request.user.is_authenticated else None
                    )

                resultado = {
                    'status': 'success',
                    'mensaje': 'Ingreso Autorizado' if tipo == RegistroMovimiento.INGRESO else 'Salida Autorizada',
                    'vehiculo': qr.vehiculo,
                    'tipo': tipo,
                    'movimiento': movimiento
                }
        except CodigoQR.DoesNotExist:
            resultado = {'status': 'danger', 'mensaje': 'Código no válido'}

        template_name = 'qr/validar_success.html' if resultado['status'] == 'success' else 'qr/validar_failure.html'
        return render(request, template_name, {'resultado': resultado})

    return render(request, 'qr/validar.html', {'resultado': resultado})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_administrador())
def configuracion_qr_view(request):
    configuracion = ConfiguracionQR.get_solo()
    if request.method == 'POST':
        form = ConfiguracionQRForm(request.POST, instance=configuracion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración QR actualizada correctamente.')
            return redirect('qr:configuracion_qr')
    else:
        form = ConfiguracionQRForm(instance=configuracion)

    return render(request, 'qr/configuracion_qr.html', {'form': form})
