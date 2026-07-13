import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.vehiculos.models import Vehiculo

class CodigoQR(models.Model):
    id_codigo_qr = models.AutoField(primary_key=True)
    
    # Relación 1 a 1: Un vehículo -> Un QR
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='codigo_qr')
    
    # El contenido será un código UUID generado aleatoriamente
    contenido = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Campo para almacenar la imagen del código QR físicamente
    imagen = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    activo = models.BooleanField(default=True)

    # SOBRESCRITURA DEL MÉTODO SAVE (POO Avanzada)
    def save(self, *args, **kwargs):
        # 1. Definir expiración (Ejemplo: 30 días si no se especifica otra)
        if not self.fecha_expiracion:
            self.fecha_expiracion = timezone.now() + timedelta(days=30)
            
        # 2. Generar el archivo de imagen del QR automáticamente si no existe
        if not self.imagen:
            # Configuramos la matriz del QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            # Le pasamos nuestro código UUID convertido a texto
            qr.add_data(str(self.contenido))
            qr.make(fit=True)
            
            # Dibujamos la imagen (blanco y negro)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardamos la imagen temporalmente en memoria (Buffer)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            
            # Nombramos el archivo y lo guardamos en el ImageField de Django
            nombre_archivo = f'qr_{self.vehiculo.placa}_{str(self.contenido)[:8]}.png'
            self.imagen.save(nombre_archivo, File(buffer), save=False)
            
        # Finalmente, llamamos al método save original para que guarde los datos en MySQL
        super().save(*args, **kwargs)

    def __str__(self):
        return f"QR {self.vehiculo.placa} - {'Activo' if self.activo else 'Inactivo'}"

    class Meta:
        verbose_name = "Código QR"
        verbose_name_plural = "Códigos QR"
        db_table = "codigo_qr"

    def renovar(self):
        # 1. Generar nuevo UUID
        self.contenido = uuid.uuid4()
        
        # 2. Borrar archivo físico anterior para no llenar el servidor de basura
        if self.imagen:
            self.imagen.delete(save=False)
            self.imagen = None
        
        # 3. Actualizar fechas
        self.fecha_expiracion = timezone.now() + timedelta(days=30)
        self.activo = True # Aseguramos que quede activo
        
        # 4. Guardar cambios. El método save() automático generará la nueva imagen
        self.save()