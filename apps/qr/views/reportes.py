"""Vistas de EXPORTACIÓN del historial (CSV, Excel, PDF y datos de gráficos)."""
from django.http import JsonResponse
from django.views import View

from apps.core.mixins import SeguridadOAdminRequiredMixin

from ..filters import filtrar_historial, orden_seguro
from ..services import reportes


class ExportarHistorialBaseView(SeguridadOAdminRequiredMixin, View):
    """Aplica los mismos filtros y el mismo orden de la pantalla y delega el formato al servicio."""

    def consulta(self, request):
        return filtrar_historial(request.GET).order_by(orden_seguro(request.GET), '-pk')

    def get(self, request):
        return self.exportar(request, self.consulta(request))

    def exportar(self, request, queryset):
        raise NotImplementedError


class ExportarHistorialCSVView(ExportarHistorialBaseView):
    def exportar(self, request, queryset):
        return reportes.exportar_csv(queryset)


class ExportarHistorialExcelView(ExportarHistorialBaseView):
    def exportar(self, request, queryset):
        return reportes.exportar_excel(queryset)


class ExportarHistorialPDFView(ExportarHistorialBaseView):
    def exportar(self, request, queryset):
        return reportes.exportar_pdf(
            queryset, filtros=reportes.descripcion_filtros(request.GET), usuario=request.user)


class DatosReporteHistorialView(SeguridadOAdminRequiredMixin, View):
    """JSON para los gráficos de la pantalla de reportes (respeta los mismos filtros)."""

    def get(self, request):
        return JsonResponse(reportes.datos_graficos(filtrar_historial(request.GET), request.GET))
