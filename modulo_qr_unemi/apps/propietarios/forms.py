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

    def clean(self):
        cleaned_data = super().clean()
        numero_identidad = cleaned_data.get('numero_identidad')
        correo = cleaned_data.get('correo')

        if numero_identidad:
            propietario_qs = Propietario.objects.filter(numero_identidad=numero_identidad)
            if self.instance.pk:
                propietario_qs = propietario_qs.exclude(pk=self.instance.pk)
            if propietario_qs.exists():
                self.add_error('numero_identidad', 'Ya existe un propietario con esta identidad.')

        if correo:
            correo_qs = Propietario.objects.filter(correo=correo)
            if self.instance.pk:
                correo_qs = correo_qs.exclude(pk=self.instance.pk)
            if correo_qs.exists():
                self.add_error('correo', 'Ya existe un propietario con este correo.')

        return cleaned_data
        