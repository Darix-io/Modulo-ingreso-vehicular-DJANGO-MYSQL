from django import forms

from .models import ConfiguracionQR
from .validadores import DIAS_MAXIMO, DIAS_MINIMO, validar_dias_vigencia

CLASES_NUMERO = (
    'w-20 border-0 bg-transparent p-0 text-center font-mono text-2xl font-bold text-brand-neutral '
    'focus:outline-none focus:ring-0 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none'
)
CLASES_INTERRUPTOR = 'peer sr-only'


class ConfiguracionQRForm(forms.ModelForm):
    """Solo los parámetros que el sistema realmente aplica: validación, vigencia y renovación automática."""

    class Meta:
        model = ConfiguracionQR
        fields = ['activar_qr', 'expiration_days', 'renovacion_automatica']
        labels = {
            'activar_qr': 'Validación de QR activada',
            'expiration_days': 'Días de vigencia del QR',
            'renovacion_automatica': 'Renovación automática',
        }
        widgets = {
            'activar_qr': forms.CheckboxInput(attrs={'class': CLASES_INTERRUPTOR}),
            'expiration_days': forms.NumberInput(attrs={
                'class': CLASES_NUMERO, 'min': DIAS_MINIMO, 'max': DIAS_MAXIMO, 'inputmode': 'numeric'}),
            'renovacion_automatica': forms.CheckboxInput(attrs={'class': CLASES_INTERRUPTOR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El campo numérico del modelo pone min=0 por su cuenta; aquí se fijan los límites reales
        self.fields['expiration_days'].widget.attrs.update(min=DIAS_MINIMO, max=DIAS_MAXIMO)

    def clean_expiration_days(self):
        return validar_dias_vigencia(self.cleaned_data.get('expiration_days'))
