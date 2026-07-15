from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    role_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.role_required:
            user = request.user
            allowed = False

            if user.is_superuser:
                allowed = True
            elif self.role_required == 'Administrador':
                allowed = user.is_administrador()
            elif self.role_required == 'Personal Seguridad':
                allowed = user.is_personal_seguridad()
            elif self.role_required == 'Seguridad o Administrador':
                allowed = user.is_administrador() or user.is_personal_seguridad()

            if not allowed:
                raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)
