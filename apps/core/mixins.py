"""
Mixins de permisos reutilizables para las vistas basadas en clases.

Uso:
    class MiVista(AdminRequiredMixin, ListView):
        ...
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .roles import ADMINISTRADOR, SEGURIDAD_O_ADMIN, tiene_rol


class RoleRequiredMixin(LoginRequiredMixin):
    """Exige iniciar sesión y tener uno de los roles de `roles_permitidos`."""
    roles_permitidos = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not tiene_rol(request.user, self.roles_permitidos):
            raise PermissionDenied('No tienes permiso para acceder a esta sección.')
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    roles_permitidos = (ADMINISTRADOR,)


class SeguridadOAdminRequiredMixin(RoleRequiredMixin):
    roles_permitidos = SEGURIDAD_O_ADMIN
