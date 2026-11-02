"""
Configuración BASE del proyecto.

Aquí va todo lo que es IGUAL en desarrollo y en producción.
Los archivos dev.py y prod.py importan este archivo y solo cambian
lo necesario (DEBUG, seguridad, etc.).

Los valores sensibles (claves, contraseñas) se leen del archivo .env
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# config/settings/base.py -> subimos 3 niveles para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env')


def env_bool(nombre, por_defecto=False):
    """Lee una variable de entorno como True/False."""
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ('1', 'true', 'yes', 'si', 'sí')


def env_list(nombre, por_defecto=''):
    """Lee una variable de entorno separada por comas como lista."""
    valor = os.environ.get(nombre, por_defecto)
    return [item.strip() for item in valor.split(',') if item.strip()]


# --------------------------------------------------------------------------
# Seguridad (dev.py y prod.py ajustan estos valores)
# --------------------------------------------------------------------------
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
DEBUG = False
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')


# --------------------------------------------------------------------------
# Aplicaciones
# --------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.core',          # Utilidades compartidas: roles, mixins, templatetags
    'apps.usuarios',      # Login, roles y panel de control
    'apps.propietarios',  # CRUD de propietarios
    'apps.vehiculos',     # CRUD de vehículos
    'apps.qr',            # Códigos QR, control de acceso, historial y reportes
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

AUTH_USER_MODEL = 'usuarios.Usuario'

# Permite iniciar sesión con correo O con nombre de usuario
AUTHENTICATION_BACKENDS = [
    'apps.usuarios.backends.EmailOrUsernameBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# --------------------------------------------------------------------------
# Base de datos: SQLite
# Toda la información se guarda en un solo archivo (db.sqlite3) dentro del
# proyecto. No hay que instalar ningún servidor: basta con tener Python.
# --------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / os.environ.get('DB_NAME', 'db.sqlite3'),
    }
}


# --------------------------------------------------------------------------
# Contraseñas
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --------------------------------------------------------------------------
# Idioma y zona horaria
# --------------------------------------------------------------------------
LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True


# --------------------------------------------------------------------------
# Archivos estáticos y media
# --------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # Se genera con collectstatic (NO se sube a Git)

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'           # Aquí se guardan las imágenes QR


# --------------------------------------------------------------------------
# Autenticación
# --------------------------------------------------------------------------
LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'usuarios:dashboard'
LOGOUT_REDIRECT_URL = 'usuarios:login'


# --------------------------------------------------------------------------
# Configuración propia del sistema
# --------------------------------------------------------------------------
# URL que se guarda dentro de cada imagen QR (el celular abre esta dirección)
VALIDACION_URL_BASE = os.environ.get('VALIDACION_URL_BASE', 'http://localhost:8000')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
