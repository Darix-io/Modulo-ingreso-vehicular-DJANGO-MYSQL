from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Vehiculo
from .forms import VehiculoForm

class VehiculoListView(LoginRequiredMixin, ListView):
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    # Usamos select_related para optimizar la consulta SQL (JOIN automático con Propietario)
    queryset = Vehiculo.objects.select_related('propietario').all()

class VehiculoCreateView(LoginRequiredMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def form_valid(self, form):
        messages.success(self.request, 'Vehículo registrado exitosamente.')
        return super().form_valid(form)

class VehiculoUpdateView(LoginRequiredMixin, UpdateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def form_valid(self, form):
        messages.info(self.request, 'Vehículo actualizado correctamente.')
        return super().form_valid(form)

class VehiculoDeleteView(LoginRequiredMixin, DeleteView):
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_confirm_delete.html'
    success_url = reverse_lazy('vehiculos:lista')

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, 'Vehículo eliminado del sistema.')
        return super().delete(request, *args, **kwargs)