from django.db import models


class Propietario(models.Model):
    TIPO_CHOICES = (
        ('Estudiante', 'Estudiante'),
        ('Docente', 'Docente'),
        ('Administrativo', 'Administrativo'),
        ('Visitante', 'Visitante'),
    )

    id_propietario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name='Nombre Completo')
    numero_identidad = models.CharField(max_length=20, unique=True, verbose_name='Cédula o ID')
    celular = models.CharField(max_length=20)
    correo = models.EmailField(max_length=100, unique=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='Estudiante')

    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Propietario'
        verbose_name_plural = 'Propietarios'
        db_table = 'propietario'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f'{self.nombre} - {self.numero_identidad} ({self.tipo})'

    # --- Reglas de negocio del propio propietario ---
    def activar(self):
        """Activa al propietario. Devuelve True si hubo cambio."""
        if self.estado:
            return False
        self.estado = True
        self.save(update_fields=['estado'])
        return True

    def desactivar(self):
        """Desactiva al propietario. Devuelve True si hubo cambio."""
        if not self.estado:
            return False
        self.estado = False
        self.save(update_fields=['estado'])
        return True
