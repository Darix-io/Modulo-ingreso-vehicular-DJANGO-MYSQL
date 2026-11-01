from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.qr.services.estadisticas import resumen_dashboard

from .forms import LoginForm


class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm      # <- antes faltaba esta línea
    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        # Sin "Recordarme": la sesión termina al cerrar el navegador
        if not form.cleaned_data.get('recordarme'):
            self.request.session.set_expiry(0)
        return respuesta


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    La vista solo arma la página.
    Los cálculos del panel están en apps/qr/services/estadisticas.py
    """
    template_name = 'usuarios/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(resumen_dashboard())
        return context


@require_POST
def logout_view(request):
    """Cerrar sesión cambia datos, por eso solo acepta POST (botón con csrf_token)."""
    logout(request)
    return redirect('usuarios:login')
