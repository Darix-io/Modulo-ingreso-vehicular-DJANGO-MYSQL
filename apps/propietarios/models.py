from django.db import models

class Propietario(models.Model):
    # Definimos los tipos de propietario disponibles en la UNEMI
    TIPO_CHOICES = (
        ('Estudiante', 'Estudiante'),
        ('Docente', 'Docente'),
        ('Administrativo', 'Administrativo'),
        ('Visitante', 'Visitante'),
    )

    # Respetamos el nombre de la llave primaria de tu diagrama
    id_propietario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name='Nombre Completo')
    numero_identidad = models.CharField(max_length=20, unique=True, verbose_name='Cédula o ID')
    celular = models.CharField(max_length=20)
    correo = models.EmailField(max_length=100, unique=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='Estudiante')

    # Campos de auditoría (Buena práctica recomendada)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True, verbose_name='Activo')

    def __str__(self):
        return f"{self.nombre} - {self.numero_identidad} ({self.tipo})"

    class Meta:
        verbose_name = "Propietario"
        verbose_name_plural = "Propietarios"
        db_table = "propietario" # Nombre exacto de la tabla en MySQL
        ordering = ['-fecha_registro'] # Ordena del más reciente al más antiguo