from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from apps.usuarios.mixins import RoleRequiredMixin
from .models import Vehiculo
from .forms import VehiculoForm

class VehiculoListView(RoleRequiredMixin, ListView):
    role_required = 'Seguridad o Administrador'
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    paginate_by = 10
    queryset = Vehiculo.objects.select_related('propietario').all()

    STATE_MAP = {
        'autorizado': 'AUTORIZADO',
        'no_autorizado': 'NO_AUTORIZADO',
        'suspendido': 'SUSPENDIDO',
    }

    def get_queryset(self):
        queryset = self.queryset
        query = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '').strip().lower()

        if query:
            queryset = queryset.filter(
                Q(placa__icontains=query) |
                Q(propietario__nombre__icontains=query) |
                Q(propietario__numero_identidad__icontains=query)
            )

        if estado in self.STATE_MAP:
            queryset = queryset.filter(estado=self.STATE_MAP[estado])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['estado_filter'] = self.request.GET.get('estado', '').strip().lower()
        return context

class VehiculoCreateView(RoleRequiredMixin, CreateView):
    role_required = 'Administrador'
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def form_valid(self, form):
        messages.success(self.request, 'Vehículo registrado exitosamente.')
        return super().form_valid(form)

class VehiculoUpdateView(RoleRequiredMixin, UpdateView):
    role_required = 'Administrador'
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def form_valid(self, form):
        messages.info(self.request, 'Vehículo actualizado correctamente.')
        return super().form_valid(form)

class VehiculoDeleteView(RoleRequiredMixin, DeleteView):
    role_required = 'Administrador'
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_confirm_delete.html'
    success_url = reverse_lazy('vehiculos:lista')

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, 'Vehículo eliminado del sistema.')
        return super().delete(request, *args, **kwargs)

class VehiculoActivateView(RoleRequiredMixin, View):
    role_required = 'Seguridad o Administrador'

    def get(self, request, pk, *args, **kwargs):
        vehiculo = get_object_or_404(Vehiculo, pk=pk)
        if vehiculo.estado != 'AUTORIZADO':
            vehiculo.estado = 'AUTORIZADO'
            vehiculo.save()
            messages.success(request, f'Vehículo {vehiculo.placa} activado exitosamente.')
        else:
            messages.info(request, f'El vehículo {vehiculo.placa} ya está autorizado.')
        return redirect('vehiculos:lista')

class VehiculoDeactivateView(RoleRequiredMixin, View):
    role_required = 'Seguridad o Administrador'

    def get(self, request, pk, *args, **kwargs):
        vehiculo = get_object_or_404(Vehiculo, pk=pk)
        if vehiculo.estado != 'NO_AUTORIZADO':
            vehiculo.estado = 'NO_AUTORIZADO'
            vehiculo.save()
            messages.warning(request, f'Vehículo {vehiculo.placa} desactivado exitosamente.')
        else:
            messages.info(request, f'El vehículo {vehiculo.placa} ya está desactivado.')
        return redirect('vehiculos:lista')
