"""Vista de la CONFIGURACIÓN de los códigos QR (solo administrador)."""
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from apps.core.mixins import AdminRequiredMixin

from ..forms import ConfiguracionQRForm
from ..models import ConfiguracionQR


class ConfiguracionQRView(AdminRequiredMixin, UpdateView):
    form_class = ConfiguracionQRForm
    template_name = 'qr/configuracion_qr.html'
    success_url = reverse_lazy('qr:configuracion_qr')

    def get_object(self, queryset=None):
        return ConfiguracionQR.get_solo()

    def form_valid(self, form):
        messages.success(self.request, 'Configuración QR actualizada correctamente.')
        return super().form_valid(form)
