"""
Las vistas de la app QR están divididas por tema:
    codigos.py       -> listar, ver, descargar y renovar QR
    accesos.py       -> validar QR, movimientos e historial
    reportes.py      -> exportar CSV / Excel / PDF y datos de gráficos
    configuracion.py -> configuración del sistema QR

Aquí se re-exportan para poder escribir `from .views import X` en urls.py
"""
from .accesos import (
    HistorialListView,
    HistorialReporteView,
    RegistroMovimientoListView,
    ValidarAccesoView,
)
from .codigos import QrDetailView, QrDownloadView, QrListView, QrRenovarView
from .configuracion import ConfiguracionQRView
from .reportes import (
    DatosReporteHistorialView,
    ExportarHistorialCSVView,
    ExportarHistorialExcelView,
    ExportarHistorialPDFView,
)

__all__ = [
    'QrListView', 'QrDetailView', 'QrDownloadView', 'QrRenovarView',
    'ValidarAccesoView', 'RegistroMovimientoListView',
    'HistorialListView', 'HistorialReporteView',
    'ExportarHistorialCSVView', 'ExportarHistorialExcelView',
    'ExportarHistorialPDFView', 'DatosReporteHistorialView',
    'ConfiguracionQRView',
]
