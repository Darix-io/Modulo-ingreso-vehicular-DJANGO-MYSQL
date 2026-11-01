"""Vistas del CONTROL DE ACCESO: validar QR, movimientos e historial."""
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from apps.core.mixins import SeguridadOAdminRequiredMixin

from ..filters import filtrar_historial, orden_alterno, orden_seguro
from ..models import RegistroMovimiento
from ..services.codigos import vigencia_qr
from ..services.garita import ultimos_accesos
from ..services.validacion import validar_acceso, validar_por_placa


class ValidarAccesoView(SeguridadOAdminRequiredMixin, View):
    """
    Pantalla de la garita. Exige iniciar sesión: antes cualquier persona con el
    enlace del QR podía registrar ingresos sin ser guardia.
    Sin parámetros muestra el escáner y el ingreso manual; con `?token=` (QR) o
    `?placa=` (respaldo manual) valida y muestra el resultado.
    Toda la lógica está en services/validacion.py
    """

    def get(self, request):
        token = request.GET.get('token')
        placa = request.GET.get('placa')

        if token:
            return self.resultado(request, validar_acceso(token, request.user))
        if placa is not None and placa.strip():
            return self.resultado(request, validar_por_placa(placa, request.user))

        accesos = ultimos_accesos()
        return render(request, 'qr/validar.html', {
            'ultimo_acceso': accesos[0] if accesos else None,
            'accesos_recientes': accesos,
            'error_placa': 'Escribe la placa del vehículo.' if placa is not None else '',
        })

    def resultado(self, request, resultado):
        plantilla = 'qr/validar_success.html' if resultado.autorizado else 'qr/validar_failure.html'
        vigencia = vigencia_qr(resultado.codigo_qr) if resultado.codigo_qr else None
        return render(request, plantilla, {'resultado': resultado, 'vigencia': vigencia})


class RegistroMovimientoListView(SeguridadOAdminRequiredMixin, ListView):
    template_name = 'qr/movimientos.html'
    context_object_name = 'movimientos'
    paginate_by = 10

    def get_queryset(self):
        queryset = RegistroMovimiento.objects.select_related(
            'vehiculo', 'codigo_qr', 'usuario_validador',
        )
        placa = self.request.GET.get('vehiculo', '').strip()
        if placa:
            queryset = queryset.filter(vehiculo__placa__iexact=placa)
        return queryset


class HistorialFiltroMixin:
    """Comparte filtros, orden y contexto entre Historial y Reporte."""

    def get_queryset(self):
        return filtrar_historial(self.request.GET).order_by(orden_seguro(self.request.GET))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get = self.request.GET
        orden = orden_seguro(get)
        context.update({
            'search_query': get.get('q', ''),
            'placa_filter': get.get('placa', ''),
            'validador_filter': get.get('validador', ''),
            'fecha_inicio': get.get('fecha_inicio', ''),
            'fecha_final': get.get('fecha_final', ''),
            'orden': orden,
            'orden_vehiculo': orden_alterno(orden, 'vehiculo__placa'),
            'orden_fecha': orden_alterno(orden, 'fecha_ingreso'),
            'orden_validador': orden_alterno(orden, 'usuario_validador__username'),
            # El paginador ya contó los registros: no se repite la consulta
            'total_registros': context['paginator'].count if context.get('paginator') else 0,
        })
        return context


class HistorialListView(SeguridadOAdminRequiredMixin, HistorialFiltroMixin, ListView):
    template_name = 'qr/historial.html'
    context_object_name = 'historial'
    paginate_by = 10


class HistorialReporteView(SeguridadOAdminRequiredMixin, HistorialFiltroMixin, ListView):
    template_name = 'qr/reporte_historial.html'
    context_object_name = 'historial'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop('page', None)
        query = f'?{params.urlencode()}' if params else ''
        base = self.request.path
        context.update({
            'csv_url': f'{base}csv/{query}',
            'excel_url': f'{base}xlsx/{query}',
            'pdf_url': f'{base}pdf/{query}',
            'chart_data_url': f'{base}datos/{query}',
        })
        return context
