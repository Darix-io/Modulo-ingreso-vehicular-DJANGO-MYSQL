"""Vistas de los CÓDIGOS QR: listar, ver, descargar y renovar."""
import os

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.mixins import SeguridadOAdminRequiredMixin

from ..models import CodigoQR


class QrListView(SeguridadOAdminRequiredMixin, ListView):
    template_name = 'qr/qr_list.html'
    context_object_name = 'qrs'
    paginate_by = 10

    def get_queryset(self):
        return CodigoQR.objects.select_related('vehiculo__propietario').order_by('-fecha_creacion')


class QrDetailView(SeguridadOAdminRequiredMixin, DetailView):
    template_name = 'qr/qr_detail.html'
    context_object_name = 'qr'
    queryset = CodigoQR.objects.select_related('vehiculo__propietario')


class QrDownloadView(SeguridadOAdminRequiredMixin, View):

    def get(self, request, pk):
        codigo_qr = get_object_or_404(CodigoQR, pk=pk)
        if not codigo_qr.imagen:
            raise Http404('Imagen de QR no disponible')
        try:
            archivo = codigo_qr.imagen.open('rb')
        except FileNotFoundError:
            raise Http404('Archivo de QR no encontrado')
        return FileResponse(archivo, as_attachment=True, filename=os.path.basename(codigo_qr.imagen.name))


class QrRenovarView(SeguridadOAdminRequiredMixin, View):
    """Solo POST: renovar cambia datos, no debe ocurrir al abrir un enlace."""
    http_method_names = ['post']

    def post(self, request, pk):
        codigo_qr = get_object_or_404(CodigoQR.objects.select_related('vehiculo'), pk=pk)
        codigo_qr.renovar()
        messages.success(request, f'Código QR del vehículo {codigo_qr.vehiculo.placa} renovado con éxito.')

        # Volver a la página desde donde se pulsó el botón (solo si es de nuestro sitio)
        siguiente = request.POST.get('next', '')
        if siguiente and url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
            return redirect(siguiente)
        return redirect('qr:lista')
