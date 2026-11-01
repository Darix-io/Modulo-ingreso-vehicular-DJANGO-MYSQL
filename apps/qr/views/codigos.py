"""Vistas de los CÓDIGOS QR: listar, ver, descargar, imprimir la credencial y renovar."""
import os

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.mixins import SeguridadOAdminRequiredMixin

from ..models import CodigoQR
from ..services import codigos as servicio


class QrListView(SeguridadOAdminRequiredMixin, ListView):
    template_name = 'qr/qr_list.html'
    context_object_name = 'qrs'
    paginate_by = 10

    def _parametros(self):
        estado = self.request.GET.get('estado', '').strip().lower()
        return self.request.GET.get('q', '').strip(), estado if estado in servicio.ESTADOS_URL else ''

    def _base(self):
        queryset = CodigoQR.objects.select_related('vehiculo__propietario')
        return servicio.buscar_codigos(queryset, self._parametros()[0])

    def get_queryset(self):
        estado = self._parametros()[1]
        queryset = servicio.filtrar_por_estado(self._base(), estado, timezone.now())
        return queryset.order_by('fecha_expiracion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ahora = timezone.now()
        q, estado = self._parametros()
        servicio.anotar_vigencia(context['qrs'], ahora)
        context.update({
            'search_query': q,
            'estado_filter': estado,
            # Los contadores respetan la búsqueda, pero no el estado elegido
            'contadores': servicio.contadores_qr(self._base(), ahora),
            'dias_por_vencer': servicio.DIAS_POR_VENCER,
        })
        return context


class QrDetailView(SeguridadOAdminRequiredMixin, DetailView):
    template_name = 'qr/qr_detail.html'
    context_object_name = 'qr'
    queryset = CodigoQR.objects.select_related('vehiculo__propietario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ahora = timezone.now()
        context['vigencia'] = servicio.vigencia_qr(self.object, ahora)
        context['accesos'] = servicio.resumen_accesos(self.object.vehiculo, ahora)
        return context


class QrCredencialView(SeguridadOAdminRequiredMixin, DetailView):
    """Página limpia, pensada para imprimirse y pegarse en el parabrisas."""
    template_name = 'qr/credencial.html'
    context_object_name = 'qr'
    queryset = CodigoQR.objects.select_related('vehiculo__propietario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vigencia'] = servicio.vigencia_qr(self.object)
        return context


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
