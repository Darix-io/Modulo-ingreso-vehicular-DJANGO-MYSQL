from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.mixins import AdminRequiredMixin, SeguridadOAdminRequiredMixin

from .forms import PropietarioForm
from .models import Propietario


class PropietarioListView(SeguridadOAdminRequiredMixin, ListView):
    model = Propietario
    template_name = 'propietarios/propietario_list.html'
    context_object_name = 'propietarios'
    paginate_by = 10

    def _filtros(self):
        get = self.request.GET
        return {
            'q': get.get('q', '').strip(),
            'tipo': get.get('tipo', '').strip(),
            'estado': get.get('estado', '').strip().lower(),
        }

    def get_queryset(self):
        filtros = self._filtros()
        queryset = super().get_queryset()

        if filtros['q']:
            queryset = queryset.filter(
                Q(nombre__icontains=filtros['q'])
                | Q(numero_identidad__icontains=filtros['q'])
                | Q(correo__icontains=filtros['q'])
            )
        if filtros['tipo']:
            queryset = queryset.filter(tipo=filtros['tipo'])
        if filtros['estado'] == 'activo':
            queryset = queryset.filter(estado=True)
        elif filtros['estado'] == 'inactivo':
            queryset = queryset.filter(estado=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtros = self._filtros()
        context.update({
            'search_query': filtros['q'],
            'tipo_filter': filtros['tipo'],
            'estado_filter': filtros['estado'],
            'tipo_choices': Propietario.TIPO_CHOICES,
        })
        return context


class PropietarioCreateView(AdminRequiredMixin, CreateView):
    model = Propietario
    form_class = PropietarioForm
    template_name = 'propietarios/propietario_form.html'
    success_url = reverse_lazy('propietarios:lista')

    def form_valid(self, form):
        messages.success(self.request, 'Propietario registrado exitosamente.')
        return super().form_valid(form)


class PropietarioUpdateView(AdminRequiredMixin, UpdateView):
    model = Propietario
    form_class = PropietarioForm
    template_name = 'propietarios/propietario_form.html'
    success_url = reverse_lazy('propietarios:lista')

    def form_valid(self, form):
        messages.info(self.request, 'Propietario actualizado correctamente.')
        return super().form_valid(form)


class PropietarioDeleteView(AdminRequiredMixin, DeleteView):
    model = Propietario
    template_name = 'propietarios/propietario_confirm_delete.html'
    success_url = reverse_lazy('propietarios:lista')

    # En Django 4+ el borrado pasa por form_valid (el antiguo delete() ya no se llamaba,
    # por eso el mensaje nunca aparecía).
    def form_valid(self, form):
        messages.warning(self.request, 'Propietario eliminado del sistema.')
        return super().form_valid(form)


class PropietarioActivateView(AdminRequiredMixin, View):
    """Solo acepta POST: un simple enlace (GET) ya no puede cambiar datos."""
    http_method_names = ['post']

    def post(self, request, pk):
        propietario = get_object_or_404(Propietario, pk=pk)
        if propietario.activar():
            messages.success(request, f'Propietario {propietario.nombre} activado correctamente.')
        else:
            messages.info(request, f'El propietario {propietario.nombre} ya está activo.')
        return redirect('propietarios:lista')


class PropietarioDeactivateView(AdminRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        propietario = get_object_or_404(Propietario, pk=pk)
        if propietario.desactivar():
            messages.warning(request, f'Propietario {propietario.nombre} desactivado. Sus vehículos no podrán ingresar.')
        else:
            messages.info(request, f'El propietario {propietario.nombre} ya está inactivo.')
        return redirect('propietarios:lista')
