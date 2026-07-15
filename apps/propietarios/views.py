from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from apps.usuarios.mixins import RoleRequiredMixin
from .models import Propietario
from .forms import PropietarioForm

# Vista para Listar (Read)
class PropietarioListView(RoleRequiredMixin, ListView):
    role_required = 'Seguridad o Administrador'
    model = Propietario
    template_name = 'propietarios/propietario_list.html'
    context_object_name = 'propietarios'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        tipo = self.request.GET.get('tipo', '').strip()
        estado = self.request.GET.get('estado', '').strip().lower()

        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) |
                Q(numero_identidad__icontains=query) |
                Q(correo__icontains=query)
            )

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if estado == 'activo':
            queryset = queryset.filter(estado=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(estado=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['tipo_filter'] = self.request.GET.get('tipo', '').strip()
        context['estado_filter'] = self.request.GET.get('estado', '').strip().lower()
        context['tipo_choices'] = Propietario.TIPO_CHOICES
        return context

# Vista para Crear (Create)
class PropietarioCreateView(RoleRequiredMixin, CreateView):
    role_required = 'Administrador'
    model = Propietario
    form_class = PropietarioForm
    template_name = 'propietarios/propietario_form.html'
    success_url = reverse_lazy('propietarios:lista')

    def form_valid(self, form):
        messages.success(self.request, 'Propietario registrado exitosamente.')
        return super().form_valid(form)

# Vista para Editar (Update)
class PropietarioUpdateView(RoleRequiredMixin, UpdateView):
    role_required = 'Administrador'
    model = Propietario
    form_class = PropietarioForm
    template_name = 'propietarios/propietario_form.html'
    success_url = reverse_lazy('propietarios:lista')

    def form_valid(self, form):
        messages.info(self.request, 'Propietario actualizado correctamente.')
        return super().form_valid(form)

# Vista para Eliminar (Delete)
class PropietarioDeleteView(RoleRequiredMixin, DeleteView):
    role_required = 'Administrador'
    model = Propietario
    template_name = 'propietarios/propietario_confirm_delete.html'
    success_url = reverse_lazy('propietarios:lista')

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, 'Propietario eliminado del sistema.')
        return super().delete(request, *args, **kwargs)


class PropietarioActivateView(RoleRequiredMixin, View):
    role_required = 'Administrador'

    def get(self, request, pk, *args, **kwargs):
        propietario = get_object_or_404(Propietario, pk=pk)
        if not propietario.estado:
            propietario.estado = True
            propietario.save()
            messages.success(request, f'Propietario {propietario.nombre} activado correctamente.')
        else:
            messages.info(request, f'El propietario {propietario.nombre} ya está activo.')
        return redirect('propietarios:lista')


class PropietarioDeactivateView(RoleRequiredMixin, View):
    role_required = 'Administrador'

    def get(self, request, pk, *args, **kwargs):
        propietario = get_object_or_404(Propietario, pk=pk)
        if propietario.estado:
            propietario.estado = False
            propietario.save()
            messages.warning(request, f'Propietario {propietario.nombre} desactivado correctamente.')
        else:
            messages.info(request, f'El propietario {propietario.nombre} ya está inactivo.')
        return redirect('propietarios:lista')
