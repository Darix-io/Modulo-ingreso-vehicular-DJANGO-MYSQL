from django.urls import path

from . import views

app_name = 'qr'

# Los nombres (name=...) son los MISMOS de antes, así las plantillas no cambian.
urlpatterns = [
    # Códigos QR
    path('', views.QrListView.as_view(), name='lista'),
    path('detalle/<int:pk>/', views.QrDetailView.as_view(), name='detalle'),
    path('descargar/<int:pk>/', views.QrDownloadView.as_view(), name='descargar'),
    path('renovar/<int:pk>/', views.QrRenovarView.as_view(), name='renovar'),
    path('configuracion/', views.ConfiguracionQRView.as_view(), name='configuracion_qr'),

    # Control de acceso
    path('validar/', views.ValidarAccesoView.as_view(), name='validar'),
    path('movimientos/', views.RegistroMovimientoListView.as_view(), name='movimientos'),
    path('historial/', views.HistorialListView.as_view(), name='historial'),

    # Reportes
    path('reportes/historial/', views.HistorialReporteView.as_view(), name='reporte_historial'),
    path('reportes/historial/csv/', views.ExportarHistorialCSVView.as_view(), name='reporte_historial_csv'),
    path('reportes/historial/xlsx/', views.ExportarHistorialExcelView.as_view(), name='reporte_historial_excel'),
    path('reportes/historial/pdf/', views.ExportarHistorialPDFView.as_view(), name='reporte_historial_pdf'),
    path('reportes/historial/datos/', views.DatosReporteHistorialView.as_view(), name='reporte_historial_datos'),
]
