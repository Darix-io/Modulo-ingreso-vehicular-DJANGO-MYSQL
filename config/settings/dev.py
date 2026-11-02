"""
Configuración de DESARROLLO (tu computadora).
Es la que usa `python manage.py runserver` por defecto.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

# En desarrollo se permite una clave por defecto para que el proyecto arranque
# aunque no tengas el .env. ¡Nunca uses esta clave en producción!
SECRET_KEY = SECRET_KEY or 'django-insecure-solo-para-desarrollo-local'  # noqa: F405

ALLOWED_HOSTS = ALLOWED_HOSTS or ['localhost', '127.0.0.1']  # noqa: F405
