from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from apps.propietarios.models import Propietario
from apps.vehiculos.models import Vehiculo
from apps.qr.models import ConfiguracionQR, HistorialIngreso, RegistroMovimiento, CodigoQR

class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True

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

        movimientos_hoy = RegistroMovimiento.objects.filter(fecha__gte=inicio, fecha__lt=fin).select_related('vehiculo', 'codigo_qr', 'usuario_validador')
        context['autorizados_hoy'] = movimientos_hoy.filter(estado='AUTORIZADO').count()
        context['denegados_hoy'] = movimientos_hoy.filter(estado='DENEGADO').count()
        context['qr_proximos_vencer'] = CodigoQR.objects.filter(activo=True, fecha_expiracion__lte=timezone.now() + timedelta(days=3)).count()
        context['recent_movements'] = movimientos_hoy.order_by('-fecha')[:5]

        labels = []
        autorizados = []
        denegados = []
        for hour in range(6, 19, 2):
            hour_start = timezone.make_aware(datetime.combine(hoy, time(hour)))
            hour_end = timezone.make_aware(datetime.combine(hoy, time(hour + 2)))
            labels.append(f'{hour:02d}:00')
            autorizados.append(movimientos_hoy.filter(estado='AUTORIZADO', fecha__gte=hour_start, fecha__lt=hour_end).count())
            denegados.append(movimientos_hoy.filter(estado='DENEGADO', fecha__gte=hour_start, fecha__lt=hour_end).count())

        context['access_chart_labels'] = labels
        context['access_chart_autorizados'] = autorizados
        context['access_chart_denegados'] = denegados

        return context


def logout_view(request):
    logout(request)
    return redirect('usuarios:login')