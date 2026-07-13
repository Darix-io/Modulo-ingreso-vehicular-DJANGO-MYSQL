from django import forms
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
        