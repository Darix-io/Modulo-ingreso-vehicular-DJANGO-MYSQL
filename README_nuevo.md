# Módulo de Ingreso Vehicular

Este proyecto es una aplicación Django para gestionar propietarios, vehículos, usuarios y QR de acceso vehicular.

## Requisitos previos

Antes de instalar, asegúrate de tener:

- Python 3.10 o superior
- Git
- MySQL Server corriendo localmente
- Un cliente de línea de comandos para Git Bash, PowerShell o CMD

## Clonar el proyecto

```bash
git clone <url-del-repositorio>
cd modulo_qr_unemi
```

## 1) Crear y activar entorno virtual

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Windows Git Bash

```bash
python -m venv venv
source venv/Scripts/activate
```

## 2) Instalar dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Preparar variables de entorno

Copia el archivo de ejemplo:

```bash
copy .env.example .env
```

Si usas Git Bash:

```bash
cp .env.example .env
```

Ajusta los valores para tu máquina:

```env
DJANGO_SECRET_KEY=tu_secret_key_segura
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=db_control_acceso
DB_USER=root
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=3306

VALIDACION_URL_BASE=http://localhost:8000
```

## 4) Crear la base de datos en MySQL

```sql
CREATE DATABASE db_control_acceso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 5) Ejecutar migraciones

```bash
python manage.py migrate
```

## 6) Crear superusuario

```bash
python manage.py createsuperuser
```

## 7) Ejecutar el proyecto

```bash
python manage.py runserver
```

Abre:

- http://127.0.0.1:8000/

## 8) Verificación rápida

```bash
python manage.py check
```

Salida esperada:

```text
System check identified no issues (0 silenced).
```

## 9) Comandos útiles

```bash
python manage.py expirar_qr
python manage.py renovar_qr_expirados
python manage.py run_qr_maintenance
```

## 10) Solución de errores comunes

### Error de conexión a MySQL

- Verifica que MySQL esté corriendo.
- Confirma que la base de datos existe.
- Revisa el archivo `.env` para sus credenciales.

### Error de módulo no encontrado

```bash
pip install -r requirements.txt
```

### Error al arrancar Django

```bash
python manage.py check
```

## Estado verificado

Se comprobó que este flujo funciona:

```bash
python -m venv venv
pip install -r requirements.txt
python manage.py check
python manage.py runserver
```
