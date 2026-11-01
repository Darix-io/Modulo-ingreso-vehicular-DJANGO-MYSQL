from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """
    Formulario de login. Solo define cómo se ven los campos.
    La validación (correo o usuario) la hace EmailOrUsernameBackend.
    """
    username = forms.CharField(
        label='Correo institucional o usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg border-0 bg-white rounded-end-4 py-3',
            'placeholder': 'correo@unemi.edu.ec',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg border-0 bg-white rounded-end-4 py-3',
            'placeholder': 'Ingrese su contraseña',
        }),
    )

    error_messages = {
        'invalid_login': 'Correo/usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta está desactivada.',
    }
