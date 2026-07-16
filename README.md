# README de instalación - Módulo de Ingreso Vehicular

Este documento explica, de forma detallada y paso a paso, cómo instalar y ejecutar el proyecto Django del sistema de ingreso vehicular en un entorno local para desarrollo.

## 1. Descripción general

El proyecto es una aplicación web desarrollada con Django 5, pensada para gestionar:

- propietarios
- vehículos
- usuarios del sistema
- códigos QR
- validación de ingreso
- historial y movimiento de accesos

La configuración principal del proyecto está en:

- `config/settings.py`
- `manage.py`

> Importante: el proyecto está configurado por defecto para usar MySQL, no SQLite.

---

## 2. Requisitos previos

Antes de instalar, asegúrate de tener instalado lo siguiente:

### 2.1. Software necesario

- Python 3.10 o superior (recomendado 3.11 o 3.12)
- Git
- MySQL Server 8.x o MariaDB
- MySQL Workbench o acceso a la línea de comandos de MySQL
- Entorno virtual de Python (`venv`)

### 2.2. Herramientas recomendadas para Windows

- Git Bash o PowerShell
- Visual Studio Build Tools (si `mysqlclient` falla al instalarse)
- XAMPP / WAMP / MySQL Server instalado en el equipo

---

## 3. Clonar el repositorio

Abre una terminal y ubícate en la carpeta donde quieres guardar el proyecto.

```bash
git clone <URL_DEL_REPOSITORIO>
cd modulo_qr_unemi
```

Si ya están trabajando dentro del repositorio, solo deben entrar a la carpeta raíz del proyecto:

```bash
cd modulo_qr_unemi
```

---

## 4. Crear entorno virtual

Es recomendable crear un entorno virtual para aislar las dependencias del proyecto.

### En Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### En Windows (Command Prompt)

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### En Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

> Si aparece un error por permisos en PowerShell, ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## 5. Instalar dependencias

Una vez activado el entorno virtual, instala los paquetes del proyecto:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Dependencias importantes

El archivo `requirements.txt` incluye:

- Django 5.0.14
- MySQL client
- Pillow
- qrcode
- reportlab
- openpyxl
- python-dotenv

Si la instalación de `mysqlclient` falla en Windows, puede requerir herramientas de compilación de C++.

### Solución común para Windows

Instala Microsoft Visual C++ Build Tools o usa una versión compatible del paquete. También puedes verificar que el servidor MySQL esté correctamente instalado.

---

## 6. Configurar variables de entorno

El proyecto usa un archivo `.env` para guardar configuración sensible y local.

### Crear el archivo `.env`

En la raíz del proyecto existe un ejemplo llamado `.env.example`.

Copia ese contenido y crea tu propio archivo `.env`:

```bash
copy .env.example .env
```

O en Linux/macOS:

```bash
cp .env.example .env
```

### Configuración recomendada

El contenido base debe quedar parecido a esto:

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

### Ajustes importantes

- `DJANGO_SECRET_KEY`: usa una clave segura en desarrollo o producción.
- `DJANGO_DEBUG`: mantén `True` para desarrollo local.
- `DB_NAME`: nombre de la base de datos MySQL.
- `DB_USER`: usuario de MySQL.
- `DB_PASSWORD`: contraseña del usuario.
- `DB_HOST`: normalmente `localhost`.
- `VALIDACION_URL_BASE`: URL base para la validación QR.

---

## 7. Crear la base de datos MySQL

Debe existir una base de datos en MySQL antes de ejecutar migraciones.

### 7.1. Acceder a MySQL

```bash
mysql -u root -p
```

### 7.2. Crear la base de datos

```sql
CREATE DATABASE db_control_acceso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
```

Si usas un nombre diferente al que está en `.env`, asegúrate de que coincida exactamente.

---

## 8. Ejecutar migraciones

Desde la raíz del proyecto:

```bash
python manage.py migrate
```

Si todo está bien, Django creará las tablas necesarias en la base de datos.

---

## 9. Crear un superusuario

Para entrar al panel administrativo de Django, crea un usuario administrador:

```bash
python manage.py createsuperuser
```

Completa los datos solicitados:

- username
- email
- password

---

## 10. Ejecutar el proyecto

Levanta el servidor local con:

```bash
python manage.py runserver
```

Luego abre en el navegador:

```text
http://127.0.0.1:8000/
```

También puedes abrir el panel administrativo en:

```text
http://127.0.0.1:8000/admin/
```

---

## 11. Generar archivos estáticos

En caso de que necesites recopilar los archivos estáticos para una verificación o despliegue:

```bash
python manage.py collectstatic --noinput
```

---

## 12. Flujo de trabajo recomendado para el equipo

Para evitar conflictos y mantener el proyecto estable:

1. Hacer `git pull` antes de trabajar.
2. Activar el entorno virtual.
3. Instalar dependencias si fue necesario.
4. Verificar que `.env` esté configurado correctamente.
5. Ejecutar migraciones si hubo cambios en el modelo.
6. Probar las funcionalidades antes de subir cambios.

---

## 13. Estructura principal del proyecto

El proyecto está organizado de la siguiente manera:

- `apps/`: módulos de la aplicación
  - `usuarios/`
  - `propietarios/`
  - `vehiculos/`
  - `qr/`
- `config/`: configuración principal de Django
- `templates/`: plantillas HTML
- `static/`: archivos CSS, JS e imágenes
- `media/`: archivos generados por la app

---

## 14. Problemas comunes y soluciones

### Error: `ModuleNotFoundError`

Esto significa que no se instalaron las dependencias o el entorno virtual no está activado.

Solución:

```bash
pip install -r requirements.txt
```

### Error: conexión a MySQL

Revisa que:

- MySQL esté corriendo
- la contraseña en `.env` sea correcta
- el nombre de la base de datos exista
- el usuario tenga permisos

### Error: `mysqlclient` no se instala

Instala herramientas de compilación de Visual Studio en Windows o usa una instalación de MySQL compatible con tu versión de Python.

### Error: `django.db.utils.OperationalError`

Generalmente indica que:

- la base de datos no existe
- el host o puerto están incorrectos
- la contraseña es inválida

---

## 15. Comandos útiles

### Iniciar servidor

```bash
python manage.py runserver
```

### Ejecutar migraciones

```bash
python manage.py migrate
```

### Crear migraciones nuevas

```bash
python manage.py makemigrations
```

### Crear superusuario

```bash
python manage.py createsuperuser
```

### Ejecutar pruebas

```bash
python manage.py test
```

---

## 16. Recomendaciones finales

- No compartas el archivo `.env` en Git.
- Mantén actualizado el entorno virtual con `pip install -r requirements.txt`.
- Si el proyecto cambió en modelos, siempre ejecuta `makemigrations` y `migrate`.
- Si alguien del equipo tiene problemas con MySQL, conviene usar la misma versión y la misma configuración de base de datos.

---

## 17. Resumen rápido de instalación

Si solo quieres una versión corta de los pasos, usa esto:

```bash
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

Si quieres, en el siguiente paso puedo ayudarte a convertir este README en una versión aún más profesional con:

- portada del proyecto
- instrucciones para Linux, Windows y macOS
- sección de despliegue
- guía para integrantes del grupo
- tabla de comandos rápidos
