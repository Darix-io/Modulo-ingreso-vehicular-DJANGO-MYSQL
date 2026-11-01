# CLAUDE.md

Sistema web de control de ingreso/salida de vehículos con códigos QR para la UNEMI.
Django 5.0 + **SQLite** (no MySQL, no instalar servidores de base de datos). Idioma del
proyecto: **español** (código de dominio, comentarios, mensajes, plantillas, commits).

## Comandos

```bash
venv\Scripts\activate                      # Windows (Linux/Mac: source venv/bin/activate)
python manage.py runserver                 # servidor de desarrollo
python manage.py test                      # pruebas (deben pasar antes de cada commit)
python manage.py check
python manage.py makemigrations --check --dry-run   # no debe detectar cambios pendientes
python manage.py migrate
python manage.py seed_roles_users          # roles + usuarios de prueba (admin, seguridad, seguridad2)
python manage.py seed_demo [--reiniciar]   # datos de demostración de Ecuador (no duplica)
python manage.py run_qr_maintenance [--renovar]     # expira (y renueva) QR vencidos
```

- `manage.py` usa `config.settings.dev`; `wsgi.py`/`asgi.py` usan `config.settings.prod`.
- Configuración sensible en `.env` (nunca se versiona; plantilla en `.env.example`).
- `db.sqlite3`, `venv/`, `.env`, `media/` y `staticfiles/` NO se suben a Git.

## Arquitectura

Monolito modular: un proyecto Django dividido en apps por dominio, y cada app en capas.

```
config/settings/{base,dev,prod}.py   Settings: lo común en base, diferencias en dev/prod
config/urls.py
apps/core/          Compartido: roles.py, mixins.py (permisos), templatetags/
apps/usuarios/      Modelo Usuario, backend de login por correo/usuario, dashboard
apps/propietarios/  CRUD de propietarios
apps/vehiculos/     CRUD de vehículos
apps/qr/
  models.py         Solo tablas y reglas pequeñas del objeto
  signals.py        Crea el QR al registrar un vehículo
  filters.py        Filtros y orden del historial
  services/         Lógica de negocio: generador, validacion, estadisticas, reportes, codigos, garita
                    (codigos.py = definición ÚNICA de vigente / por vencer / expirado / inactivo;
                    garita.py = accesos recientes de la pantalla Validar acceso)
  views/            Vistas por tema: codigos, accesos, reportes, configuracion
templates/<modulo>/ Plantillas HTML por módulo      static/  CSS
```

### Regla de las capas (obligatoria)

- Las **vistas** solo reciben la petición, llaman a un servicio/modelo y devuelven la
  respuesta. No llevan reglas de negocio.
- Las **reglas del negocio** viven en `apps/qr/services/` o en métodos del modelo.
- Los **modelos** solo definen tablas y reglas pequeñas (`is_expired`, `renovar`, `get_solo`).
- Los servicios importan modelos; si un modelo necesita un servicio, importarlo **dentro
  del método** para evitar importaciones circulares (ver `CodigoQR.save`).
- Código compartido entre apps → `apps/core/`. No importar vistas de otra app.

## Reglas del negocio

**Roles** (`apps/core/roles.py`): `Administrador` y `Personal Seguridad`. Los permisos se
aplican con los mixins de `apps/core/mixins.py` (`AdminRequiredMixin`,
`SeguridadOAdminRequiredMixin`, `RoleRequiredMixin`). Nunca comprobar roles a mano en las vistas.

**Un vehículo puede ingresar solo si se cumplen TODAS** (`services/validacion.py`,
`motivo_de_rechazo`, en este orden):
1. Validación de QR activada (`ConfiguracionQR.activar_qr`).
2. El código no ha expirado (`is_expired`). Si además está inactivo, el motivo es «Código expirado».
3. `CodigoQR.activo` es True («Código desactivado» solo si se desactivó sin haber expirado).
4. `Vehiculo.estado == AUTORIZADO` (suspendido o no autorizado → denegado).
5. `Propietario.estado` activo.
6. Quien valida inició sesión como Seguridad o Administrador (lo exige la vista).

- El motivo de un vehículo no habilitado dice exactamente «Vehículo suspendido» o «Vehículo no autorizado»
  (`MOTIVOS_POR_ESTADO`; no usar `get_estado_display()`, que dice «Acceso suspendido»).
- **Validar por placa** (`validar_por_placa`, respaldo del QR): normaliza la placa (mayúsculas, sin espacios ni guion),
  aplica las mismas reglas (`_registrar` + `motivo_de_rechazo`) y en un ingreso/salida autorizado guarda el detalle
  «Validación manual por placa»; en un denegado el detalle es el motivo real. Placa inexistente → «Placa no registrada»
  (no se guarda movimiento: no hay vehículo ni QR al que ligarlo; igual que «Código no válido»).
- La pantalla `qr:validar` es una sola, responsive: escáner con `html5-qrcode` (versión fija por CDN; valida una vez por
  lectura y vuelve con `?token=`), ingreso manual (`?placa=`), último resultado y accesos de hoy (no existe «turno»).
  Las páginas de resultado reemplazan su dirección con `history.replaceState` para que recargar no registre otro movimiento.
- Cada intento, autorizado **o denegado**, se guarda en `RegistroMovimiento`.
  `HistorialIngreso` se crea solo en ingresos autorizados.
- Ingreso y salida **alternan solos**: si el último movimiento autorizado fue INGRESO, el siguiente es SALIDA.
- El texto escaneado puede ser el UUID solo o la URL completa (`…?token=UUID`); un texto
  inválido devuelve "Código no válido", nunca un error 500 (`extraer_token`).
- Todo el registro de un movimiento va dentro de `transaction.atomic()`.
- Estados de un QR (`services/codigos.py`): vigente = activo y no expirado; por vencer = vigente que vence en
  3 días o menos; expirados o inactivos = el resto. Lista, detalle y panel usan esa misma definición.
- Un QR vencido se marca inactivo. Cada vehículo tiene un único `CodigoQR` (OneToOne), creado
  por señal al registrar el vehículo. `ConfiguracionQR` es un registro único (`get_solo()`, id=1).
- `renovar()` genera nuevo token + imagen y reinicia la expiración.

## Convenciones

- Español en nombres de dominio (`propietario`, `vehiculo`, `movimiento`), mensajes y
  comentarios. Funciones y variables en `snake_case`, clases en `PascalCase`.
- Docstrings cortos que expliquen el *por qué*; archivos de servicio abren con un docstring del flujo.
- Constantes de choices como atributos de clase (`INGRESO`, `AUTORIZADO`, …), nunca strings sueltos.
- Vistas basadas en clases con mixins de permisos; plantillas heredan de `templates/base.html`.
- Interfaz: **Tailwind (CDN) + Material Symbols**, siguiendo `INSTRUCCIONES-DISENO.md` (rediseño por
  fases). Bootstrap se carga solo en las pantallas aún no rediseñadas, vía los bloques `legacy_css` /
  `legacy_js` de `base.html`; las pantallas nuevas los dejan vacíos. Componentes reutilizables en
  `templates/includes/` (`logo`, `placa`, `badge_estado`, `avatar`). Cerrar sesión es POST.
- Formularios: los widgets usan las clases de `apps/core/estilos.py` y las plantillas pintan cada campo con
  `includes/campo_form.html` (ícono + errores); las listas usan `includes/paginacion.html` (conserva filtros).
  Las reglas de validación van en un módulo propio (ej. `propietarios/validadores.py`) y se prueban solas.
- La credencial imprimible (`qr:credencial`) es una página independiente (`credencial.css`), sin menú.
  Renovar un QR genera un token nuevo: la credencial impresa anterior deja de funcionar, por eso
  renovar es solo del administrador (`AdminRequiredMixin`, botón oculto a Seguridad). Ver, descargar e imprimir son de ambos roles.
- Eliminar con cascada: pedir confirmación explícita (casilla) y mostrar lo que realmente se borra.
- Plantillas: los botones de crear/editar/eliminar y de autorizar/desactivar (vehículos y propietarios) solo se
  muestran con `user.is_administrador`, y las vistas lo exigen con `AdminRequiredMixin` (403).
  `{# #}` es solo de una línea; para varias líneas usar `{% comment %}`.
- Zona horaria `America/Guayaquil`, `USE_TZ=True`, idioma `es-ec`.
- Todo cambio de modelo lleva su migración; `makemigrations --check` debe quedar limpio.
- Toda regla de negocio nueva lleva su prueba en `tests.py` de la app (o en un `tests_<tema>.py`, como
  `apps/qr/tests_codigos.py` y `tests_validar.py`). Todas las pruebas existentes deben seguir pasando.
- Dependencias nuevas → agregarlas a `requirements.txt`. No introducir MySQL ni otro motor.
- Git: trabajar en ramas, mensajes de commit en español, **no hacer push sin que el usuario lo pida**.
- Nunca versionar secretos ni `.env`.
