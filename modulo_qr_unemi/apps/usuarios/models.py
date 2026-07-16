from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        db_table = 'rol_enum'

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    cedula = models.CharField(max_length=20, unique=True)
    rol = models.ForeignKey(Rol, blank=True, null=True, on_delete=models.SET_NULL)

    objects = UserManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuario'

    def __str__(self):
        return self.username

    @property
    def role_name(self):
        return self.rol.nombre if self.rol else None

    def is_administrador(self):
        return self.is_superuser or self.role_name == 'Administrador'

    def is_personal_seguridad(self):
        return self.is_superuser or self.role_name == 'Personal Seguridad'


class AdministradorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(rol__nombre='Administrador')


class PersonalSeguridadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(rol__nombre='Personal Seguridad')


class Administrador(Usuario):
    objects = AdministradorManager()

    class Meta:
        proxy = True
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'


class PersonalSeguridad(Usuario):
    objects = PersonalSeguridadManager()

    class Meta:
        proxy = True
        verbose_name = 'Personal Seguridad'
        verbose_name_plural = 'Personal Seguridad'
