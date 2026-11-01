"""
Configuración de PRODUCCIÓN (servidor real).
Se activa con la variable de entorno:
    DJANGO_SETTINGS_MODULE=config.settings.prod
"""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured('Falta DJANGO_SECRET_KEY en el archivo .env')

# Cookies solo por HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
