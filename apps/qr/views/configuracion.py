"""Vista de la CONFIGURACIÓN de los códigos QR (solo administrador)."""
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView

from apps.core.mixins import AdminRequiredMixin

from ..forms import ConfiguracionQRForm
from ..models import CodigoQR, ConfiguracionQR
from ..services.codigos import DIAS_POR_VENCER, contadores_qr


class ConfiguracionQRView(AdminRequiredMixin, UpdateView):
    form_class = ConfiguracionQRForm
    template_name = 'qr/configuracion_qr.html'
    success_url = reverse_lazy('qr:configuracion_qr')

    def get_object(self, queryset=None):
        return ConfiguracionQR.get_solo()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'contadores': contadores_qr(CodigoQR.objects.all(), timezone.now()),
            'dias_por_vencer': DIAS_POR_VENCER,
        })
        return context

    def form_valid(self, form):
        if not form.has_changed():
            messages.info(self.request, 'No hubo cambios que guardar.')
            return super().form_valid(form)
        configuracion = form.cleaned_data
        messages.success(
            self.request,
            'Configuración guardada: vigencia de {dias} días, validación {validacion} y renovación automática {renovacion}.'.format(
                dias=configuracion['expiration_days'],
                validacion='activada' if configuracion['activar_qr'] else 'desactivada',
                renovacion='activada' if configuracion['renovacion_automatica'] else 'desactivada',
            ),
        )
        return super().form_valid(form)
