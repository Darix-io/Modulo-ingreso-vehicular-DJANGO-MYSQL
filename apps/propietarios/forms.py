from django import forms
from django.core.exceptions import ValidationError

from apps.core.estilos import CLASES_INPUT, CLASES_INPUT_MONO, CLASES_SELECT

from .models import Propietario
from .validadores import validar_celular, validar_documento


class PropietarioForm(forms.ModelForm):
    class Meta:
        model = Propietario
        fields = ['nombre', 'tipo', 'numero_identidad', 'celular', 'correo']
        labels = {
            'nombre': 'Nombre completo',
            'tipo': 'Tipo de propietario',
            'numero_identidad': 'Cédula de identidad',
            'celular': 'Celular de contacto',
            'correo': 'Correo electrónico',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': CLASES_INPUT, 'placeholder': 'Ej: Juan Pérez Mora', 'autofocus': True}),
            'tipo': forms.Select(attrs={'class': CLASES_SELECT}),
            'numero_identidad': forms.TextInput(attrs={'class': CLASES_INPUT_MONO, 'placeholder': '0912345678', 'inputmode': 'numeric'}),
            'celular': forms.TextInput(attrs={'class': CLASES_INPUT_MONO, 'placeholder': '0991234567', 'inputmode': 'numeric', 'maxlength': 10}),
            'correo': forms.EmailInput(attrs={'class': CLASES_INPUT, 'placeholder': 'correo@unemi.edu.ec'}),
        }
        # Django ya valida que no se repitan (unique=True en el modelo).
        # Aquí solo personalizamos el mensaje; ya no hace falta repetir la consulta a mano.
        error_messages = {
            'numero_identidad': {'unique': 'Ya existe un propietario con esta identidad.'},
            'correo': {'unique': 'Ya existe un propietario con este correo.'},
        }

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data.get('nombre', '').split())
        if len(nombre) < 3:
            raise ValidationError('Ingrese el nombre y apellido completos (mínimo 3 caracteres).')
        return nombre

    def clean_celular(self):
        return validar_celular(self.cleaned_data.get('celular', ''))

    def clean_correo(self):
        return self.cleaned_data.get('correo', '').strip().lower()

    def clean(self):
        """La regla del documento depende del tipo, por eso se revisa aquí y no campo por campo."""
        datos = super().clean()
        tipo = datos.get('tipo')
        numero = datos.get('numero_identidad')
        if tipo and numero is not None:
            try:
                datos['numero_identidad'] = validar_documento(numero, tipo)
            except ValidationError as error:
                self.add_error('numero_identidad', error)
        return datos
