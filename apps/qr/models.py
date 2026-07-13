import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User # Importamos el modelo User
from apps.vehiculos.models import Vehiculo
from django.conf import settings

class CodigoQR(models.Model):
    id_codigo_qr = models.AutoField(primary_key=True)
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='codigo_qr')
    contenido = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    imagen = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.fecha_expiracion:
            self.fecha_expiracion = timezone.now() + timedelta(days=30)
            
        if not self.imagen:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(str(self.contenido))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            
            nombre_archivo = f'qr_{self.vehiculo.placa}_{str(self.contenido)[:8]}.png'
            self.imagen.save(nombre_archivo, File(buffer), save=False)
            
        super().save(*args, **kwargs)

    def renovar(self):
        self.contenido = uuid.uuid4()
        if self.imagen:
            self.imagen.delete(save=False)
            self.imagen = None
        self.fecha_expiracion = timezone.now() + timedelta(days=30)
        self.activo = True
        self.save()

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