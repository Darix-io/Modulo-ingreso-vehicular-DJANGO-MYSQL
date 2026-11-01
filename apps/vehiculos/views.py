from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.mixins import AdminRequiredMixin, SeguridadOAdminRequiredMixin

from .forms import VehiculoForm
from .models import Vehiculo


class VehiculoListView(SeguridadOAdminRequiredMixin, ListView):
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    paginate_by = 10

    # Valor que llega en la URL (?estado=...) -> valor guardado en la BD
    ESTADOS_URL = {
        'autorizado': Vehiculo.AUTORIZADO,
        'no_autorizado': Vehiculo.NO_AUTORIZADO,
        'suspendido': Vehiculo.SUSPENDIDO,
    }

    def get_queryset(self):
        queryset = Vehiculo.objects.select_related('propietario')
        query = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '').strip().lower()

        if query:
            queryset = queryset.filter(
                Q(placa__icontains=query)
                | Q(propietario__nombre__icontains=query)
                | Q(propietario__numero_identidad__icontains=query)
            )
        if estado in self.ESTADOS_URL:
            queryset = queryset.filter(estado=self.ESTADOS_URL[estado])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['estado_filter'] = self.request.GET.get('estado', '').strip().lower()
        return context


class VehiculoCreateView(AdminRequiredMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def form_valid(self, form):
        # Al guardar, la señal de la app qr crea automáticamente su código QR
        messages.success(self.request, 'Vehículo registrado exitosamente. Su código QR fue generado.')
        return super().form_valid(form)


class VehiculoUpdateView(AdminRequiredMixin, UpdateView):
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

    def form_valid(self, form):
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
