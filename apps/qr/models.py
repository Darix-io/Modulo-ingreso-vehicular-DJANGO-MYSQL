"""
Modelos de la app QR.

Este archivo ahora SOLO define tablas y reglas pequeñas de cada objeto.
- La creación de la imagen QR está en services/generador.py
- La validación de acceso está en services/validacion.py
- La señal que crea el QR al registrar un vehículo está en signals.py
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.vehiculos.models import Vehiculo


class ConfiguracionQR(models.Model):
    """Configuración única del sistema (siempre es el registro id=1)."""
    nombre = models.CharField(max_length=100, default='Configuración QR')
    descripcion = models.TextField(blank=True, null=True)
    expiration_days = models.PositiveIntegerField(default=30)
    activar_qr = models.BooleanField(default=True)
    permitir_reutilizacion = models.BooleanField(default=False)   # sin uso: la validación no lo aplica
    renovacion_automatica = models.BooleanField(default=False)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración QR'
        verbose_name_plural = 'Configuraciones QR'

    def __str__(self):
        return self.nombre

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class CodigoQR(models.Model):
    id_codigo_qr = models.AutoField(primary_key=True)
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='codigo_qr')
    contenido = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    imagen = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Código QR'
        verbose_name_plural = 'Códigos QR'
        db_table = 'codigo_qr'

    def __str__(self):
        return f"QR {self.vehiculo.placa} - {'Activo' if self.activo else 'Inactivo'}"

    @staticmethod
    def calcular_expiracion():
        dias = ConfiguracionQR.get_solo().expiration_days
        return timezone.now() + timedelta(days=dias)

    def save(self, *args, **kwargs):
        # Import aquí para evitar importaciones circulares (services importa models)
        from .services.generador import generar_imagen_qr

        if not self.fecha_expiracion:
            self.fecha_expiracion = self.calcular_expiracion()
        if not self.imagen:
            generar_imagen_qr(self)
        if self.is_expired:
            self.activo = False
        super().save(*args, **kwargs)

    def renovar(self):
        """Genera un token nuevo, una imagen nueva y reinicia la fecha de expiración."""
        self.contenido = uuid.uuid4()
        if self.imagen:
            self.imagen.delete(save=False)
            self.imagen = None
        self.fecha_expiracion = self.calcular_expiracion()
        self.activo = True
        self.save()

    @property
    def is_expired(self):
        return bool(self.fecha_expiracion) and self.fecha_expiracion <= timezone.now()


class HistorialIngreso(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    usuario_validador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Historial de Ingreso'
        db_table = 'historial_ingreso'
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return f'{self.vehiculo.placa} - {self.fecha_ingreso:%d/%m/%Y %H:%M}'


class RegistroMovimiento(models.Model):
    INGRESO = 'INGRESO'
    SALIDA = 'SALIDA'
    TIPO_CHOICES = [
        (INGRESO, 'Ingreso'),
        (SALIDA, 'Salida'),
    ]

    AUTORIZADO = 'AUTORIZADO'
    DENEGADO = 'DENEGADO'
    ESTADO_CHOICES = [
        (AUTORIZADO, 'Autorizado'),
        (DENEGADO, 'Denegado'),
    ]

    id_movimiento = models.AutoField(primary_key=True)
    codigo_qr = models.ForeignKey(CodigoQR, on_delete=models.CASCADE, related_name='movimientos')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default=INGRESO)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default=DENEGADO)
    usuario_validador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Registro de Movimiento'
        verbose_name_plural = 'Registros de Movimiento'
        db_table = 'registro_movimiento'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.vehiculo.placa} ({self.get_estado_display()})'
