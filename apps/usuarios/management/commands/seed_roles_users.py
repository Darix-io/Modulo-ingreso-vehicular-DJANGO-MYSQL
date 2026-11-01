"""
Crea los roles y los usuarios de prueba (un administrador y dos guardias).

    python manage.py seed_roles_users

Las contraseñas se pueden cambiar en el .env con SEED_ADMIN_PASSWORD y
SEED_SEGURIDAD_PASSWORD (si no existen, se usan las de ejemplo). Los dos guardias
comparten la contraseña de seguridad.
"""
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD, TODOS_LOS_ROLES
from apps.usuarios.models import Rol, Usuario

USUARIOS_SEMILLA = [
    {
        'username': 'admin',
        'first_name': 'Carlos',
        'last_name': 'Mendoza',
        'email': 'admin@unemi.edu.ec',
        'cedula': '9999999999',
        'rol': ADMINISTRADOR,
        'is_superuser': True,
        'password_env': 'SEED_ADMIN_PASSWORD',
        'password_defecto': 'Admin1234!',
    },
    {
        'username': 'seguridad',
        'first_name': 'Víctor',
        'last_name': 'Morán',
        'email': 'seguridad@unemi.edu.ec',
        'cedula': '8888888888',
        'rol': PERSONAL_SEGURIDAD,
        'is_superuser': False,
        'password_env': 'SEED_SEGURIDAD_PASSWORD',
        'password_defecto': 'Seguridad123!',
    },
    {
        'username': 'seguridad2',
        'first_name': 'Luis',
        'last_name': 'Castro',
        'email': 'seguridad2@unemi.edu.ec',
        'cedula': '7777777777',
        'rol': PERSONAL_SEGURIDAD,
        'is_superuser': False,
        'password_env': 'SEED_SEGURIDAD_PASSWORD',
        'password_defecto': 'Seguridad123!',
    },
]


class Command(BaseCommand):
    help = 'Crea roles básicos y usuarios de ejemplo (administrador y dos guardias).'

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {}
        for nombre in TODOS_LOS_ROLES:
            rol, creado = Rol.objects.get_or_create(nombre=nombre)
            roles[nombre] = rol
            estilo = self.style.SUCCESS if creado else self.style.WARNING
            self.stdout.write(estilo(f"Rol {'creado' if creado else 'existente'}: {nombre}"))

        for datos in USUARIOS_SEMILLA:
            password = os.environ.get(datos['password_env'], datos['password_defecto'])
            usuario, creado = Usuario.objects.get_or_create(
                username=datos['username'],
                defaults={'email': datos['email'], 'cedula': datos['cedula']},
            )
            # Nombre y apellido: se completan solo si el usuario no los tiene
            if not usuario.first_name:
                usuario.first_name = datos['first_name']
            if not usuario.last_name:
                usuario.last_name = datos['last_name']
            usuario.rol = roles[datos['rol']]
            usuario.is_superuser = datos['is_superuser']
            usuario.is_staff = True
            usuario.is_active = True
            if creado:
                usuario.set_password(password)
            usuario.save()

            if creado:
                self.stdout.write(self.style.SUCCESS(
                    f"Usuario creado: {datos['username']} / {password}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Usuario existente (rol verificado): {datos['username']}"
                ))

        self.stdout.write(self.style.SUCCESS('Seed inicial completada.'))
