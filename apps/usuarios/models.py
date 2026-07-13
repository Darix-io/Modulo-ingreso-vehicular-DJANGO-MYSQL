from django.db import models
from django.contrib.auth.models import AbstractUser

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True) # Ej: Administrador, Personal_seguridad

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        db_table = "rol_enum" # Respetamos el nombre de tu diccionario de datos


class Usuario(AbstractUser):
    # AbstractUser ya nos proporciona: password, first_name, last_name, is_active, etc.
    
    # Sobrescribimos el email para que sea único, ya que será nuestra credencial de acceso
    email = models.EmailField(unique=True)
    
    # Añadimos los campos específicos de tu proyecto
    cedula = models.CharField(max_length=20, unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True)

    # Configuramos Django para que el login sea con el CORREO en lugar del username por defecto
    USERNAME_FIELD = 'email'
    # Campos que se pedirán obligatoriamente al crear un usuario por consola
    REQUIRED_FIELDS = ['username', 'cedula', 'first_name', 'last_name'] 

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.cedula}"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = "usuario"