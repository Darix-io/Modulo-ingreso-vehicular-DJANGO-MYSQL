from django.urls import path
from .views import (
    QrListView,
    QrDetailView,
    QrDownloadView,
    HistorialListView,
    HistorialReporteView,
    RegistroMovimientoListView,
    renovar_qr_view,
    validar_acceso_view,
    configuracion_qr_view,
    exportar_historial_csv,
    exportar_historial_excel,
    exportar_historial_pdf,
    datos_reporte_historial,
)

app_name = 'qr'

urlpatterns = [
    path('', QrListView.as_view(), name='lista'),
    path('detalle/<int:pk>/', QrDetailView.as_view(), name='detalle'),
    path('descargar/<int:pk>/', QrDownloadView.as_view(), name='descargar'),
    path('renovar/<int:pk>/', renovar_qr_view, name='renovar'),
    path('validar/', validar_acceso_view, name='validar'),
    path('configuracion/', configuracion_qr_view, name='configuracion_qr'),
    path('historial/', HistorialListView.as_view(), name='historial'),
    path('reportes/historial/', HistorialReporteView.as_view(), name='reporte_historial'),
    path('reportes/historial/csv/', exportar_historial_csv, name='reporte_historial_csv'),
    path('reportes/historial/xlsx/', exportar_historial_excel, name='reporte_historial_excel'),
    path('reportes/historial/pdf/', exportar_historial_pdf, name='reporte_historial_pdf'),
    path('reportes/historial/datos/', datos_reporte_historial, name='reporte_historial_datos'),
    path('movimientos/', RegistroMovimientoListView.as_view(), name='movimientos'),
]
