import re

from django import forms
from django.core.exceptions import ValidationError

from apps.core.estilos import CLASES_INPUT, CLASES_INPUT_MONO, CLASES_SELECT, CLASES_TEXTAREA
from apps.propietarios.models import Propietario

from .models import Vehiculo

PATRON_PLACA = re.compile(r'^[A-Z0-9-]+$')


class PropietarioChoiceField(forms.ModelChoiceField):
    """Muestra 'Nombre · cédula (tipo)' en el selector."""

    def label_from_instance(self, propietario):
        return f'{propietario.nombre} · {propietario.numero_identidad} ({propietario.tipo})'


class VehiculoForm(forms.ModelForm):
    propietario = PropietarioChoiceField(
        queryset=Propietario.objects.none(),
        empty_label='Selecciona un propietario',
        label='Propietario',
        widget=forms.Select(attrs={'class': CLASES_SELECT}),
    )

    class Meta:
        model = Vehiculo
        fields = ['propietario', 'placa', 'marca', 'modelo', 'color', 'anio', 'estado', 'observaciones']
        labels = {
            'placa': 'Placa',
            'anio': 'Año',
            'estado': 'Estado de acceso',
        }
        widgets = {
            'placa': forms.TextInput(attrs={
                'class': CLASES_INPUT_MONO + ' uppercase', 'placeholder': 'GSA-3841',
                'maxlength': 20, 'autocomplete': 'off', 'autofocus': True,
            }),
            'marca': forms.TextInput(attrs={'class': CLASES_INPUT, 'placeholder': 'Ej: Chevrolet'}),
            'modelo': forms.TextInput(attrs={'class': CLASES_INPUT, 'placeholder': 'Ej: Aveo'}),
            'color': forms.TextInput(attrs={'class': CLASES_INPUT, 'placeholder': 'Ej: Rojo'}),
            'anio': forms.NumberInput(attrs={'class': CLASES_INPUT, 'placeholder': 'Ej: 2020', 'min': 1900, 'max': 2100}),
            'estado': forms.Select(attrs={'class': CLASES_SELECT}),
            'observaciones': forms.Textarea(attrs={'class': CLASES_TEXTAREA, 'rows': 3, 'placeholder': 'Opcional…'}),
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
