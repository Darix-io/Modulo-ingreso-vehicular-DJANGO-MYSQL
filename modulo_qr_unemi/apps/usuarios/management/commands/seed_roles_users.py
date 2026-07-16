from django.core.management.base import BaseCommand
from apps.usuarios.models import Rol, Usuario


class Command(BaseCommand):
    help = 'Crea roles básicos y un usuario administrador de ejemplo.'

    def handle(self, *args, **options):
        roles = ['Administrador', 'Personal Seguridad']
        for nombre in roles:
            rol, created = Rol.objects.get_or_create(nombre=nombre)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Rol creado: {nombre}"))
            else:
                self.stdout.write(self.style.WARNING(f"Rol existente: {nombre}"))

        admin_email = 'admin@unemi.edu.ec'
        admin_username = 'admin'
        admin_cedula = '9999999999'
        admin_password = 'Admin1234!'

        seguridad_email = 'seguridad@unemi.edu.ec'
        seguridad_username = 'seguridad'
        seguridad_cedula = '8888888888'
        seguridad_password = 'Seguridad123!'

        admin_rol = Rol.objects.get(nombre='Administrador')
        seguridad_rol = Rol.objects.get(nombre='Personal Seguridad')

        admin_user, created = Usuario.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': admin_email,
                'cedula': admin_cedula,
                'rol': admin_rol,
                'is_superuser': True,
                'is_staff': True,
                'is_active': True,
            }
        )

        if created:
            admin_user.set_password(admin_password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Usuario administrador creado: {admin_username} / {admin_password}"
            ))
        else:
            if admin_user.rol != admin_rol or not admin_user.is_superuser or not admin_user.is_staff:
                admin_user.rol = admin_rol
                admin_user.is_superuser = True
                admin_user.is_staff = True
                admin_user.is_active = True
                admin_user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Usuario administrador actualizado: {admin_username}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Usuario administrador ya existe: {admin_username}"
                ))

        seguridad_user, created = Usuario.objects.get_or_create(
            username=seguridad_username,
            defaults={
                'email': seguridad_email,
                'cedula': seguridad_cedula,
                'rol': seguridad_rol,
                'is_superuser': False,
                'is_staff': True,
                'is_active': True,
            }
        )

        if created:
            seguridad_user.set_password(seguridad_password)
            seguridad_user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Usuario personal seguridad creado: {seguridad_username} / {seguridad_password}"
            ))
        else:
            if seguridad_user.rol != seguridad_rol or seguridad_user.is_superuser or not seguridad_user.is_staff:
                seguridad_user.rol = seguridad_rol
                seguridad_user.is_superuser = False
                seguridad_user.is_staff = True
                seguridad_user.is_active = True
                seguridad_user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Usuario personal seguridad actualizado: {seguridad_username}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Usuario personal seguridad ya existe: {seguridad_username}"
                ))

        self.stdout.write(self.style.SUCCESS('Seed inicial completada.'))
