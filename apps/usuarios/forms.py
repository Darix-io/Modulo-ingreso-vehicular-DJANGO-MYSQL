from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q

User = get_user_model()

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Correo institucional',
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

    def clean(self):
        cleaned_data = super().clean()
        username = self.data.get('username')
        password = self.data.get('password')

        if not username or not password:
            return cleaned_data

        user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).first()
        if user is None:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

        self.user_cache = authenticate(
            request=self.request,
            username=user.get_username(),
            password=password,
        )

        if self.user_cache is None:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

        if not self.user_cache.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

        cleaned_data['username'] = user.get_username()
        cleaned_data['password'] = password
        return cleaned_data