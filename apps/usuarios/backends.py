"""
Backend de autenticación: permite entrar con el CORREO o con el USUARIO.

Antes esto se intentaba hacer dentro del formulario de login, pero el
formulario llamaba primero a la validación normal de Django (que solo
acepta username) y fallaba antes de probar con el correo.
Un "backend" es la forma oficial de Django para cambiar cómo se valida
un usuario. Se activa en settings con AUTHENTICATION_BACKENDS.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

UserModel = get_user_model()


class EmailOrUsernameBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if not username or not password:
            return None

        usuario = (
            UserModel.objects
            .filter(Q(username__iexact=username) | Q(email__iexact=username))
            .order_by('pk')
            .first()
        )

        if usuario is None:
            # Se calcula un hash igual, para no revelar por el tiempo de
            # respuesta si el usuario existe o no.
            UserModel().set_password(password)
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
