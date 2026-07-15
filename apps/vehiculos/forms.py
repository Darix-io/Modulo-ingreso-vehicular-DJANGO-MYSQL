import re
from django import forms
from django.core.exceptions import ValidationError

from .models import Vehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['propietario', 'placa', 'marca', 'modelo', 'color', 'anio', 'estado', 'observaciones']
        widgets = {
            # Django convertirá 'propietario' en un <select> automáticamente
            'propietario': forms.Select(attrs={'class': 'form-select'}),
            'placa': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Ej: ABC-1234'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Chevrolet'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Aveo'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Rojo'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2020'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Opcional...'}),
        }

    def clean_placa(self):
        placa = self.cleaned_data.get('placa', '').strip().upper()
        if not placa:
            raise ValidationError('La placa es obligatoria.')
        if not re.match(r'^[A-Z0-9-]+$', placa):
            raise ValidationError('La placa solo puede contener letras, números y guiones.')

        vehiculos = Vehiculo.objects.filter(placa=placa)
        if self.instance.pk:
            vehiculos = vehiculos.exclude(pk=self.instance.pk)
        if vehiculos.exists():
            raise ValidationError('Ya existe un vehículo con esta placa.')

        return placa

    def clean_anio(self):
        anio = self.cleaned_data.get('anio')
        if anio is not None and (anio < 1900 or anio > 2100):
            raise ValidationError('Ingrese un año válido entre 1900 y 2100.')
        return anio
