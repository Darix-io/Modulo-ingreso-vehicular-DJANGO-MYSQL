from django.apps import AppConfig


class CoreConfig(AppConfig):
    """App sin modelos: guarda el código que comparten todos los módulos."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Núcleo compartido'
