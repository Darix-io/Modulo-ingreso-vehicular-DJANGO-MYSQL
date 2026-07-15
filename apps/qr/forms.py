from django import forms
from .models import ConfiguracionQR


class ConfiguracionQRForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionQR
        fields = [
            'nombre',
            'descripcion',
            'expiration_days',
            'activar_qr',
            'permitir_reutilizacion',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'expiration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'activar_qr': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permitir_reutilizacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'expiration_days': 'Número de días que permanecerá válido un código QR desde su creación o renovación.',
            'activar_qr': 'Si está deshabilitado, ningún QR podrá ser validado hasta reactivar esta opción.',
            'permitir_reutilizacion': 'Permitir que un mismo QR pueda usarse varias veces antes de expirar.',
        }
