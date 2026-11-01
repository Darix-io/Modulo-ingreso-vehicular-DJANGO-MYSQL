from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.mixins import AdminRequiredMixin, SeguridadOAdminRequiredMixin
from apps.propietarios.models import Propietario

from .filters import contadores_por_estado, filtrar_vehiculos, leer_filtros
from .forms import VehiculoForm
from .models import Vehiculo
from .services import resumen_eliminacion


class VehiculoListView(SeguridadOAdminRequiredMixin, ListView):
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    paginate_by = 10

    def get_queryset(self):
        return filtrar_vehiculos(leer_filtros(self.request.GET))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtros = leer_filtros(self.request.GET)
        context.update({
            'search_query': filtros['q'],
            'estado_filter': filtros['estado'],
            'contadores': contadores_por_estado(filtros),
            'total_registros': Vehiculo.objects.count(),
        })
        return context


class VehiculoFormMixin:
    """Datos extra que necesita la pantalla del formulario."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sin propietarios activos no se puede registrar un vehículo: la pantalla lo explica
        context['hay_propietarios'] = Propietario.objects.filter(estado=True).exists()
        return context


class VehiculoCreateView(AdminRequiredMixin, VehiculoFormMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def form_valid(self, form):
        # Al guardar, la señal de la app qr crea automáticamente su código QR
        messages.success(self.request, 'Vehículo registrado exitosamente. Su código QR fue generado.')
        return super().form_valid(form)


class VehiculoUpdateView(AdminRequiredMixin, VehiculoFormMixin, UpdateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def form_valid(self, form):
        messages.info(self.request, 'Vehículo actualizado correctamente.')
        return super().form_valid(form)


class VehiculoDeleteView(AdminRequiredMixin, DeleteView):
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_confirm_delete.html'
    success_url = reverse_lazy('vehiculos:lista')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resumen'] = resumen_eliminacion(self.object)
        return context

    def form_valid(self, form):
        # Borrar es irreversible: además del botón deshabilitado en pantalla, se exige aquí
        if not self.request.POST.get('confirmo'):
            messages.error(self.request, 'Marca la casilla de confirmación para eliminar el vehículo.')
            return redirect('vehiculos:eliminar', pk=self.object.pk)
        messages.warning(self.request, 'Vehículo eliminado del sistema.')
        return super().form_valid(form)


class VehiculoActivateView(SeguridadOAdminRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        vehiculo = get_object_or_404(Vehiculo, pk=pk)
        if vehiculo.cambiar_estado(Vehiculo.AUTORIZADO):
            messages.success(request, f'Vehículo {vehiculo.placa} activado exitosamente.')
        else:
            messages.info(request, f'El vehículo {vehiculo.placa} ya está autorizado.')
        return redirect('vehiculos:lista')


class VehiculoDeactivateView(SeguridadOAdminRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        vehiculo = get_object_or_404(Vehiculo, pk=pk)
        if vehiculo.cambiar_estado(Vehiculo.NO_AUTORIZADO):
            messages.warning(request, f'Vehículo {vehiculo.placa} desactivado exitosamente.')
        else:
            messages.info(request, f'El vehículo {vehiculo.placa} ya está desactivado.')
        return redirect('vehiculos:lista')
