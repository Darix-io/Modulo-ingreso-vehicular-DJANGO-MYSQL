from django.shortcuts import redirect
from django.views import View


class HomeRedirectView(View):
    """La raíz del sitio ('/') manda al panel o al login."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('usuarios:dashboard')
        return redirect('usuarios:login')
