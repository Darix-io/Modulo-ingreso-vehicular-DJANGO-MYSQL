from django import forms
from django.contrib.auth.forms import AuthenticationForm

CLASES_INPUT = (
    'w-full rounded-lg border border-outline-variant/60 bg-white py-3 pl-11 pr-11 text-on-surface '
    'shadow-sm placeholder:text-outline focus:border-primary-container focus:outline-none '
    'focus:ring-2 focus:ring-primary-container/15'
)


class LoginForm(AuthenticationForm):
    """
    Formulario de login. Solo define cómo se ven los campos.
    La validación (correo o usuario) la hace EmailOrUsernameBackend.
    """
    username = forms.CharField(
        label='Correo institucional o usuario',
        widget=forms.TextInput(attrs={
            'class': CLASES_INPUT,
            'placeholder': 'ej. usuario@unemi.edu.ec',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': CLASES_INPUT,
            'placeholder': '••••••••••••',
        }),
    )
    # Si no se marca, la sesión termina al cerrar el navegador (lo aplica la vista)
    recordarme = forms.BooleanField(
        label='Recordarme',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 cursor-pointer rounded border-outline-variant accent-primary-container',
        }),
    )

    error_messages = {
        'invalid_login': 'Correo/usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta está desactivada.',
    }
