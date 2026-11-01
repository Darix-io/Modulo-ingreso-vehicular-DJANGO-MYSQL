from django.shortcuts import redirect, render
from django.views import View


class HomeRedirectView(View):
    """La raíz del sitio ('/') manda al panel o al login."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('usuarios:dashboard')
        return redirect('usuarios:login')


def previsualizar_error(request, codigo):
    """
    Solo en desarrollo (DEBUG=True): permite ver las páginas de error con la marca,
    porque con DEBUG Django muestra su propia pantalla técnica en lugar de 403.html, 404.html y 500.html.
    """
    return render(request, f'{codigo}.html', status=codigo)
