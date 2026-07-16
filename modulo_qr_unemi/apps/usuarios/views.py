from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from django.contrib import messages
from apps.propietarios.models import Propietario
from apps.vehiculos.models import Vehiculo
from apps.qr.models import ConfiguracionQR, HistorialIngreso
from .forms import LoginForm

class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True
    form_class = LoginForm
    success_url = 'usuarios:dashboard'

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        if user is None:
            # Permitir autenticación por email si el usuario no se encuentra por username.
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=username)
            except User.DoesNotExist:
                user_obj = None
            if user_obj is not None:
                user = authenticate(self.request, username=user_obj.username, password=password)
        if user is not None:
            login(self.request, user)
            return redirect(self.get_success_url())
        messages.error(self.request, 'Correo o contraseña incorrectos.')
        return self.form_invalid(form)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        inicio = timezone.make_aware(datetime.combine(hoy, time.min))
        fin = inicio + timedelta(days=1)

        context['total_propietarios'] = Propietario.objects.count()
        context['total_vehiculos'] = Vehiculo.objects.count()
        context['total_accesos'] = HistorialIngreso.objects.count()
        configuracion = ConfiguracionQR.get_solo()
        context['qr_expiration_days'] = configuracion.expiration_days
        context['qr_activada'] = configuracion.activar_qr
        context['qr_reutilizable'] = configuracion.permitir_reutilizacion
        context['ingresos_hoy'] = HistorialIngreso.objects.filter(fecha_ingreso__gte=inicio, fecha_ingreso__lt=fin).count()
        inicioayer = inicio - timedelta(days=1)
        context['ingresos_ayer'] = HistorialIngreso.objects.filter(fecha_ingreso__gte=inicioayer, fecha_ingreso__lt=inicio).count()
        context['diferencia_ingresos'] = context['ingresos_hoy'] - context['ingresos_ayer']

        inicio_semana_actual = inicio - timedelta(days=hoy.weekday())
        inicio_semana_pasada = inicio_semana_actual - timedelta(days=7)
        context['ingresos_semana_actual'] = HistorialIngreso.objects.filter(fecha_ingreso__gte=inicio_semana_actual).count()
        context['ingresos_semana_pasada'] = HistorialIngreso.objects.filter(fecha_ingreso__gte=inicio_semana_pasada, fecha_ingreso__lt=inicio_semana_actual).count()
        context['diferencia_semana'] = context['ingresos_semana_actual'] - context['ingresos_semana_pasada']

        inicio_mes_actual = timezone.make_aware(datetime.combine(hoy.replace(day=1), time.min))
        if hoy.month == 1:
            inicio_mes_pasado = timezone.make_aware(datetime.combine(date(hoy.year - 1, 12, 1), time.min))
        else:
            inicio_mes_pasado = timezone.make_aware(datetime.combine(date(hoy.year, hoy.month - 1, 1), time.min))
        context['ingresos_mes_actual'] = HistorialIngreso.objects.filter(fecha_ingreso__gte=inicio_mes_actual).count()
        context['ingresos_mes_pasado'] = HistorialIngreso.objects.filter(fecha_ingreso__gte=inicio_mes_pasado, fecha_ingreso__lt=inicio_mes_actual).count()
        context['diferencia_mes'] = context['ingresos_mes_actual'] - context['ingresos_mes_pasado']
        return context


def logout_view(request):
    logout(request)
    return redirect('usuarios:login')