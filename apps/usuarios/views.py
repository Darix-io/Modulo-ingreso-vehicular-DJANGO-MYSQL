from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.qr.services.estadisticas import resumen_dashboard

from .forms import LoginForm


class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm      # <- antes faltaba esta línea
    redirect_authenticated_user = True


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


def logout_view(request):
    logout(request)
    return redirect('usuarios:login')
