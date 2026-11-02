# GaritaQR — Módulo de ingreso vehicular con códigos QR (UNEMI)

Sistema web en **Django 5 + SQLite** para controlar el ingreso y la salida de vehículos del campus
mediante códigos QR. Cada vehículo registrado recibe su QR automáticamente; en la garita se escanea con
la cámara (o se escribe la placa si el QR está dañado) y el sistema autoriza o deniega el paso y deja el
registro.

## Qué hace

- **Inicio de sesión** con correo institucional o usuario, y dos roles: **Administrador** y **Personal de Seguridad**.
- **Propietarios** (estudiantes, docentes, administrativos, visitantes) y **vehículos**, con contadores, búsqueda y
  confirmación al eliminar (se muestra todo lo que se borra en cascada).
- **Códigos QR**: lista con estados (activos, por vencer, expirados o inactivos), detalle con resumen de accesos,
  **credencial imprimible** y renovación.
- **Validar acceso** (garita): escáner con la cámara, ingreso manual por placa como respaldo, resultado
  autorizado o denegado con el motivo real. Ingreso y salida se alternan solos.
- **Movimientos** (todos los intentos, autorizados y denegados), **Historial** (solo ingresos autorizados) y
  **Reportes** con gráficos y descargas en **PDF, Excel y CSV** que respetan los filtros.
- **Configuración QR** (solo administrador): validación activada o no, días de vigencia y renovación automática.
- **Panel de control** con las cifras de hoy, de la semana y del mes.
- Páginas de error 403, 404 y 500 con la marca del sistema.

## Quién ve qué

| Pantalla | Administrador | Personal de Seguridad |
|---|---|---|
| Panel, Validar acceso, Movimientos, Historial, Reportes | Sí | Sí |
| Propietarios, Vehículos, Códigos QR (ver, descargar, imprimir) | Sí | Solo ver (sin crear, editar ni eliminar) |
| Autorizar o desactivar vehículos y propietarios, renovar QR | Sí | No (403) |
| Configuración QR | Sí | No (403) |

## Reglas de acceso

Un vehículo puede ingresar solo si se cumplen **todas**, en este orden:

1. La validación de QR está activada en Configuración QR.
2. El código no ha expirado.
3. El código está activo (no fue desactivado).
4. El vehículo está en estado **Autorizado** (suspendido o no autorizado → denegado).
5. El propietario está **activo**.
6. Quien valida inició sesión como Seguridad o Administrador.

Cada intento queda en *Movimientos*, autorizado o denegado, con su motivo («Código expirado», «Vehículo suspendido»,
«Vehículo no autorizado», «Propietario inactivo»…). El historial guarda solo los ingresos autorizados. La validación
por placa aplica exactamente las mismas reglas que el QR.

## Arquitectura

Monolito modular: un solo proyecto Django dividido en apps por dominio, y cada app separada en capas.

```
config/
  settings/            base.py (común), dev.py (manage.py), prod.py (wsgi.py y asgi.py)
  urls.py
apps/
  core/                Código compartido: roles, mixins de permisos, estilos de formularios, templatetags
  usuarios/            Login (por correo o usuario), roles, panel de control
  propietarios/        CRUD de propietarios (validadores propios de cédula y celular)
  vehiculos/           CRUD de vehículos
  qr/
    models.py          Solo tablas y reglas pequeñas
    signals.py         Crea el QR al registrar un vehículo
    filters.py         Filtros y orden de movimientos e historial
    forms.py           Formulario de Configuración QR (validadores en validadores.py)
    services/          Lógica de negocio
      validacion.py      Reglas de acceso (QR y placa)
      codigos.py         Definición única de vigente / por vencer / expirado / inactivo
      estadisticas.py    Números del panel
      movimientos.py     Contadores de hoy
      garita.py          Accesos recientes de la pantalla Validar acceso
      reportes.py        Gráficos, CSV, Excel y PDF con la marca
      mantenimiento.py   Expirar y renovar QR vencidos
      generador.py       Imagen del QR
    views/             Vistas por tema: codigos, accesos, reportes, configuracion
templates/             Plantillas por módulo; includes/ con los componentes reutilizables
static/                CSS propio y credencial imprimible
```

**Regla de las capas:** las vistas reciben la petición y devuelven la respuesta; las reglas del negocio viven en
`services/` o en métodos del modelo. Interfaz con **Tailwind (CDN)** y **Material Symbols**; no usa Bootstrap.

## Instalación

No necesitas instalar ninguna base de datos: SQLite viene con Python y guarda todo en `db.sqlite3`.

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # Linux/Mac: cp .env.example .env  (y cambia los valores)
python manage.py migrate
python manage.py seed_roles_users
python manage.py seed_demo       # opcional: datos de demostración
python manage.py runserver
```

Abre http://127.0.0.1:8000/ e inicia sesión.

### Usuarios de prueba (`seed_roles_users`)

| Rol | Usuario o correo | Contraseña |
|---|---|---|
| Administrador | `admin` / `admin@unemi.edu.ec` | `Admin1234!` |
| Personal de Seguridad | `seguridad` / `seguridad@unemi.edu.ec` | `Seguridad123!` |
| Personal de Seguridad | `seguridad2` / `seguridad2@unemi.edu.ec` | `Seguridad123!` |

Las contraseñas se cambian en `.env` (`SEED_ADMIN_PASSWORD`, `SEED_SEGURIDAD_PASSWORD`). **Cámbialas antes de usar el
sistema de verdad.**

### Datos de demostración (`seed_demo`)

```bash
python manage.py seed_demo           # crea 15 propietarios, 20 vehículos con QR y 30 días de movimientos
python manage.py seed_demo --reset   # borra SOLO los datos de demostración y los vuelve a crear con fechas de hoy
```

Funciona incluso sobre una base recién migrada (crea los roles y usuarios que falten). No duplica datos: si ya
existen, no hace nada. Con `--reset` los movimientos de «hoy» se generan entre las 06:00 y la hora actual, así que
conviene ejecutarlo durante el día. No toca usuarios ni configuración.

## Tarea programada (mantenimiento de los QR)

Los QR vencen. El comando de mantenimiento los marca como inactivos y, si en **Configuración QR** está activada la
**renovación automática**, renueva los de vehículos autorizados con propietario activo (la credencial impresa anterior
deja de servir). Hay que programarlo en el servidor, una vez al día:

```bash
python manage.py run_qr_maintenance            # expira; renueva solo si la renovación automática está activada
python manage.py run_qr_maintenance --renovar  # fuerza la renovación aunque esté desactivada
```

Windows (Programador de tareas, cada noche a las 02:00):

```
schtasks /Create /SC DAILY /ST 02:00 /TN "GaritaQR mantenimiento" /TR "C:\ruta\venv\Scripts\python.exe C:\ruta\manage.py run_qr_maintenance"
```

Linux (cron):

```
0 2 * * * /ruta/venv/bin/python /ruta/manage.py run_qr_maintenance
```

## Cámara y celular

El escáner usa la cámara del navegador, que solo está disponible en **`localhost` o con HTTPS**. Si la cámara no
funciona, la pantalla Validar acceso lo explica y deja disponible la validación por placa. Cada QR contiene una
dirección con el código; para que apunte a tu servidor, pon su dirección en `VALIDACION_URL_BASE` del `.env`.

## Pruebas y comandos útiles

| Comando | Qué hace |
|---|---|
| `python manage.py test` | Ejecuta todas las pruebas (deben pasar antes de cada commit) |
| `python manage.py check` | Revisa la configuración |
| `python manage.py makemigrations --check --dry-run` | No debe detectar cambios pendientes |
| `python manage.py seed_roles_users` | Crea los roles y los usuarios de prueba |
| `python manage.py seed_demo [--reset]` | Datos de demostración |
| `python manage.py run_qr_maintenance [--renovar]` | Mantenimiento de los QR |

En desarrollo (`DEBUG=True`) puedes ver las páginas de error en `/errores/403/`, `/errores/404/` y `/errores/500/`.

## Rediseño por fases

La interfaz se rediseñó siguiendo `INSTRUCCIONES-DISENO.md`, una fase por vez:

1. Sistema de diseño, menú, componentes y login. 2. Panel de control. 3. Propietarios. 4. Vehículos.
5. Códigos QR (lista, detalle y credencial). 6. Validar acceso (cámara, placa y resultados). 7. Movimientos,
historial y reportes. 8. Configuración QR. 9. Revisión final: páginas de error, sin Bootstrap, revisión a 400, 768 y
escritorio, pantallas vacías y documentación.

## Tecnologías

Django 5.0 · SQLite · Tailwind CSS · Chart.js · html5-qrcode · qrcode · ReportLab · openpyxl · Pillow
