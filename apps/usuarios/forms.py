from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    # Aunque internamente Django lo llama 'username', nosotros le pasamos un EmailInput
    username = forms.CharField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg border-0 bg-white rounded-end-4 py-3',
            'placeholder': 'correo@unemi.edu.ec',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg border-0 bg-white rounded-end-4 py-3',
            'placeholder': 'Ingrese su contraseña'
        })
    )