from django.apps import AppConfig


class QrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.qr'
    verbose_name = 'Códigos QR y control de acceso'

    def ready(self):
        # Registra las señales (crear QR al crear un vehículo)
        from . import signals  # noqa: F401
