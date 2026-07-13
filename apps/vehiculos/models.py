from django.db import models
from apps.propietarios.models import Propietario

class Vehiculo(models.Model):
    # Estados de autorización estandarizados
    ESTADO_CHOICES = (
        ('AUTORIZADO', 'Autorizado para ingresar'),
        ('NO_AUTORIZADO', 'No autorizado'),
        ('SUSPENDIDO', 'Acceso suspendido'),
    )

    id_vehiculo = models.AutoField(primary_key=True)
    
    # AQUÍ ESTÁ LA MAGIA DE LA RELACIÓN 1:N
    # on_delete=models.CASCADE significa que si borramos al propietario, se borran sus vehículos
    propietario = models.ForeignKey(
        Propietario, 
        on_delete=models.CASCADE, 
        related_name='vehiculos',
        verbose_name='Propietario del Vehículo'
    )
    
    placa = models.CharField(max_length=20, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='AUTORIZADO')
    
    # Campos adicionales recomendados para el sistema real
    anio = models.PositiveIntegerField(verbose_name='Año', null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        db_table = "vehiculo"
        ordering = ['-fecha_registro']