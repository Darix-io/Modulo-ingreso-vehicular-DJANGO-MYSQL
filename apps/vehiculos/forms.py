import re

from django import forms
from django.core.exceptions import ValidationError

from apps.propietarios.models import Propietario

from .models import Vehiculo

PATRON_PLACA = re.compile(r'^[A-Z0-9-]+$')


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['propietario', 'placa', 'marca', 'modelo', 'color', 'anio', 'estado', 'observaciones']
        widgets = {
            'propietario': forms.Select(attrs={'class': 'form-select'}),
            'placa': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Ej: ABC-1234'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Chevrolet'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Aveo'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Rojo'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2020'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Opcional...'}),
        }
        error_messages = {
            'placa': {'unique': 'Ya existe un vehículo con esta placa.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo se pueden elegir propietarios activos (y el actual, si se está editando)
        activos = Propietario.objects.filter(estado=True)
        if self.instance.pk:
            activos = activos | Propietario.objects.filter(pk=self.instance.propietario_id)
        self.fields['propietario'].queryset = activos.distinct().order_by('nombre')

    def clean_placa(self):
        placa = self.cleaned_data.get('placa', '').strip().upper()
        if not placa:
            raise ValidationError('La placa es obligatoria.')
        if not PATRON_PLACA.match(placa):
            raise ValidationError('La placa solo puede contener letras, números y guiones.')
        return placa

    def clean_anio(self):
        anio = self.cleaned_data.get('anio')
        if anio is not None and not (1900 <= anio <= 2100):
            raise ValidationError('Ingrese un año válido entre 1900 y 2100.')
        return anio
