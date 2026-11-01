# Módulo de Ingreso Vehicular QR — UNEMI

Sistema web en **Django + SQLite** para controlar el ingreso y salida de vehículos
al campus mediante códigos QR.

## Funcionalidades

- Inicio de sesión con correo institucional o usuario, con dos roles: **Administrador** y **Personal de Seguridad**.
- CRUD de **propietarios** (estudiantes, docentes, administrativos, visitantes).
- CRUD de **vehículos**; al registrar uno se genera su **código QR** automáticamente.
- **Control de acceso** en garita: al escanear el QR se registra ingreso o salida (alternan solos).
- Historial de ingresos con filtros, reportes con gráficos y exportación a **CSV, Excel y PDF**.
- Panel de control con estadísticas del día, semana y mes.

## Arquitectura

Monolito modular: un solo proyecto Django dividido en apps por dominio, y cada app
separada en capas.

```
config/
  settings/
    base.py        Configuración común
    dev.py         Desarrollo (la usa manage.py)
    prod.py        Producción (la usan wsgi.py y asgi.py)
  urls.py
apps/
  core/            Código compartido: roles, mixins de permisos, templatetags
  usuarios/        Login (backend por correo), roles, panel de control
  propietarios/    CRUD de propietarios
  vehiculos/       CRUD de vehículos
  qr/
    models.py      Solo tablas y reglas pequeñas
    signals.py     Crea el QR al registrar un vehículo
    filters.py     Filtros y orden del historial
    services/      Lógica de negocio
      generador.py     Imagen del QR
      validacion.py    Reglas de acceso en garita
      estadisticas.py  Números del panel
      reportes.py      CSV / Excel / PDF
    views/         Vistas divididas por tema
      codigos.py, accesos.py, reportes.py, configuracion.py
templates/         Plantillas HTML por módulo
static/            CSS
```

**Regla de las capas:** las vistas reciben la petición y muestran el resultado;
las reglas del negocio viven en `services/` o en los métodos del modelo.

## Reglas de acceso

Un vehículo puede ingresar solo si se cumplen todas:

1. La validación de QR está activada en la configuración.
2. El código QR está activo y no ha expirado.
3. El vehículo está en estado **Autorizado**.
4. El propietario está **activo**.
5. Quien valida inició sesión como Seguridad o Administrador.

Cada intento queda registrado en *Movimientos*, sea autorizado o denegado.

## Instalación

No necesitas instalar ninguna base de datos: SQLite viene incluido con Python y guarda todo en el archivo `db.sqlite3`.

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # Linux/Mac: cp .env.example .env  -> editar valores
python manage.py migrate
python manage.py seed_roles_users
python manage.py runserver
```

Usuarios de prueba: `admin@unemi.edu.ec / Admin1234!` y `seguridad@unemi.edu.ec / Seguridad123!`

## Comandos útiles

| Comando | Qué hace |
|---|---|
| `python manage.py test` | Ejecuta las pruebas |
| `python manage.py run_qr_maintenance` | Marca como inactivos los QR vencidos |
| `python manage.py run_qr_maintenance --renovar` | Además renueva los QR de vehículos autorizados |
| `python manage.py expirar_qr` | Solo expira QR vencidos |

## Tecnologías

Django 5.0 · SQLite · Bootstrap 5 · qrcode · ReportLab · openpyxl
