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

# Detrás del proxy de PythonAnywhere (HTTPS): Django confía en el encabezado que indica el esquema original
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Orígenes que pueden enviar formularios (POST) por HTTPS; ej: https://usuario.pythonanywhere.com
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')  # noqa: F405

# Cookies solo por HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
