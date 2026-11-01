"""Vistas de EXPORTACIÓN del historial (CSV, Excel, PDF y datos de gráficos)."""
from django.http import JsonResponse
from django.views import View

from apps.core.mixins import SeguridadOAdminRequiredMixin

from ..filters import filtrar_historial
from ..services import reportes


class ExportarHistorialBaseView(SeguridadOAdminRequiredMixin, View):
    """Aplica los mismos filtros de la pantalla y delega el formato al servicio."""
    exportador = None   # cada subclase indica qué función del servicio usar

    def get(self, request):
        queryset = filtrar_historial(request.GET).order_by('-fecha_ingreso')
        return self.exportador(queryset)


class ExportarHistorialCSVView(ExportarHistorialBaseView):
    exportador = staticmethod(reportes.exportar_csv)


class ExportarHistorialExcelView(ExportarHistorialBaseView):
    exportador = staticmethod(reportes.exportar_excel)


class ExportarHistorialPDFView(ExportarHistorialBaseView):
    exportador = staticmethod(reportes.exportar_pdf)


class DatosReporteHistorialView(SeguridadOAdminRequiredMixin, View):

    def get(self, request):
        return JsonResponse(reportes.datos_graficos(filtrar_historial(request.GET)))
