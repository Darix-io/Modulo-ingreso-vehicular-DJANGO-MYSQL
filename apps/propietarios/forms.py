from django import forms
from django.core.exceptions import ValidationError

from .models import Propietario


class PropietarioForm(forms.ModelForm):
    class Meta:
        model = Propietario
        fields = ['nombre', 'numero_identidad', 'celular', 'correo', 'tipo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez'}),
            'numero_identidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de cédula'}),
            'celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0999999999'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@unemi.edu.ec'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }
        # Django ya valida que no se repitan (unique=True en el modelo).
        # Aquí solo personalizamos el mensaje; ya no hace falta repetir la consulta a mano.
        error_messages = {
            'numero_identidad': {'unique': 'Ya existe un propietario con esta identidad.'},
            'correo': {'unique': 'Ya existe un propietario con este correo.'},
        }

    def clean_numero_identidad(self):
        numero = self.cleaned_data.get('numero_identidad', '').strip()
        if not numero.isdigit():
            raise ValidationError('La cédula o identidad debe contener solo números.')
        return numero

    def clean_celular(self):
        celular = self.cleaned_data.get('celular', '').strip()
        if not celular.isdigit():
            raise ValidationError('El celular debe contener solo números.')
        if len(celular) < 7:
            raise ValidationError('Ingrese un número de celular válido de al menos 7 dígitos.')
        return celular

    def clean_correo(self):
        return self.cleaned_data.get('correo', '').strip().lower()
