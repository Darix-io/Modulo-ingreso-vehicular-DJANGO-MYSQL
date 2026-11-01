"""Vistas del CONTROL DE ACCESO: validar QR, movimientos e historial."""
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from apps.core.mixins import SeguridadOAdminRequiredMixin

from ..filters import filtrar_historial, orden_alterno, orden_seguro
from ..models import RegistroMovimiento
from ..services.validacion import validar_acceso


class ValidarAccesoView(SeguridadOAdminRequiredMixin, View):
    """
    Pantalla de la garita. Ahora EXIGE iniciar sesión: antes cualquier persona
    con el enlace del QR podía registrar ingresos sin ser guardia.
    Toda la lógica está en services/validacion.py
    """

    def get(self, request):
        token = request.GET.get('token')
        if not token:
            return render(request, 'qr/validar.html', {'resultado': None})

        resultado = validar_acceso(token, request.user)
        plantilla = 'qr/validar_success.html' if resultado.autorizado else 'qr/validar_failure.html'
        return render(request, plantilla, {'resultado': resultado})


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
