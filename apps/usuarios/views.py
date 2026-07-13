from django.contrib.auth.views import LoginView
from .forms import LoginForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html' # Plantilla que vamos a usar
    form_class = LoginForm # Formulario que acabamos de crear
    redirect_authenticated_user = True # Si ya ingresó, no le mostramos el login de nuevo

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/dashboard.html'
    
    # Si alguien sin sesión intenta entrar, lo enviamos al login
    login_url = 'usuarios:login'