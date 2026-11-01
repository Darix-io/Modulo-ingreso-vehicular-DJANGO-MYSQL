from django.db import models

from apps.propietarios.models import Propietario


class Vehiculo(models.Model):
    # Constantes para no escribir los textos a mano en otros archivos
    AUTORIZADO = 'AUTORIZADO'
    NO_AUTORIZADO = 'NO_AUTORIZADO'
    SUSPENDIDO = 'SUSPENDIDO'

    ESTADO_CHOICES = (
        (AUTORIZADO, 'Autorizado para ingresar'),
        (NO_AUTORIZADO, 'No autorizado'),
        (SUSPENDIDO, 'Acceso suspendido'),
    )

    id_vehiculo = models.AutoField(primary_key=True)

    # Relación 1:N -> un propietario puede tener varios vehículos
    propietario = models.ForeignKey(
        Propietario,
        on_delete=models.CASCADE,
        related_name='vehiculos',
        verbose_name='Propietario del Vehículo',
    )

    placa = models.CharField(max_length=20, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default=AUTORIZADO)

    anio = models.PositiveIntegerField(verbose_name='Año', null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        db_table = 'vehiculo'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f'{self.placa} - {self.marca} {self.modelo}'

    # --- Reglas de negocio ---
    @property
    def puede_ingresar(self):
        """Un vehículo entra solo si está autorizado Y su propietario está activo."""
        return self.estado == self.AUTORIZADO and self.propietario.estado

    def cambiar_estado(self, nuevo_estado):
        """Cambia el estado. Devuelve True si hubo cambio."""
        if self.estado == nuevo_estado:
            return False
        self.estado = nuevo_estado
        self.save(update_fields=['estado'])
        return True
