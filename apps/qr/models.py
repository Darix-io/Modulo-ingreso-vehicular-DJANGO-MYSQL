import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from apps.vehiculos.models import Vehiculo


class ConfiguracionQR(models.Model):
    nombre = models.CharField(max_length=100, default='Configuración QR')
    descripcion = models.TextField(blank=True, null=True)
    expiration_days = models.PositiveIntegerField(default=30)
    activar_qr = models.BooleanField(default=True)
    permitir_reutilizacion = models.BooleanField(default=False)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración QR'
        verbose_name_plural = 'Configuraciones QR'

    def __str__(self):
        return self.nombre

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class CodigoQR(models.Model):
    id_codigo_qr = models.AutoField(primary_key=True)
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='codigo_qr')
    contenido = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    imagen = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        config = ConfiguracionQR.get_solo()
        if not self.fecha_expiracion:
            self.fecha_expiracion = timezone.now() + timedelta(days=config.expiration_days)
            
        if not self.imagen:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            contenido = str(self.contenido)
            base_url = getattr(settings, 'VALIDACION_URL_BASE', '').rstrip('/')
            if base_url:
                qr_data = f"{base_url}/qr/validar/?token={contenido}"
            else:
                qr_data = contenido
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            nombre_archivo = f'qr_{self.vehiculo.placa}_{contenido[:8]}.png'
            self.imagen.save(nombre_archivo, File(buffer), save=False)
            
        if self.fecha_expiracion and self.fecha_expiracion <= timezone.now():
            self.activo = False

        super().save(*args, **kwargs)

    def renovar(self):
        self.contenido = uuid.uuid4()
        if self.imagen:
            self.imagen.delete(save=False)
            self.imagen = None
        config = ConfiguracionQR.get_solo()
        self.fecha_expiracion = timezone.now() + timedelta(days=config.expiration_days)
        self.activo = True
        self.save()

    @property
    def is_expired(self):
        return self.fecha_expiracion <= timezone.now()

    def __str__(self):
        return f"QR {self.vehiculo.placa} - {'Activo' if self.activo else 'Inactivo'}"

    class Meta:
        verbose_name = "Código QR"
        verbose_name_plural = "Códigos QR"
        db_table = "codigo_qr"

class HistorialIngreso(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    # Cambiamos 'auth.User' por settings.AUTH_USER_MODEL
    usuario_validador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Historial de Ingreso"
        db_table = "historial_ingreso"
        ordering = ['-fecha_ingreso']



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
        return f"{self.get_tipo_display()} - {self.vehiculo.placa} ({self.get_estado_display()})"

@receiver(post_save, sender=Vehiculo)
def crear_codigo_qr(sender, instance, created, **kwargs):
    if created:
        CodigoQR.objects.create(vehiculo=instance)
