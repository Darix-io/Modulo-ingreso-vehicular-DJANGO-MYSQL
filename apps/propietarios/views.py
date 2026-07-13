from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Propietario
from .forms import PropietarioForm

# Vista para Listar (Read)
class PropietarioListView(LoginRequiredMixin, ListView):
    model = Propietario
    template_name = 'propietarios/propietario_list.html'
    context_object_name = 'propietarios'

# Vista para Crear (Create)
class PropietarioCreateView(LoginRequiredMixin, CreateView):
    model = Propietario
    form_class = PropietarioForm
    template_name = 'propietarios/propietario_form.html'
    success_url = reverse_lazy('propietarios:lista')

    def form_valid(self, form):
        messages.success(self.request, 'Propietario registrado exitosamente.')
        return super().form_valid(form)

# Vista para Editar (Update)
class PropietarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Propietario
    form_class = PropietarioForm
    template_name = 'propietarios/propietario_form.html'
    success_url = reverse_lazy('propietarios:lista')

    def form_valid(self, form):
        messages.info(self.request, 'Propietario actualizado correctamente.')
        return super().form_valid(form)

# Vista para Eliminar (Delete)
class PropietarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Propietario
    template_name = 'propietarios/propietario_confirm_delete.html'
    success_url = reverse_lazy('propietarios:lista')

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, 'Propietario eliminado del sistema.')
        return super().delete(request, *args, **kwargs)