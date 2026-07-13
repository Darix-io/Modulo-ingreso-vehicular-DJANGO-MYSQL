from django import forms
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