# Sprint 9 - Optimización y despliegue

## Objetivo

Optimizar el rendimiento de la aplicación, completar pruebas y documentación, asegurar una interfaz responsive, y preparar el despliegue.

## Historias de usuario

- Como administrador, quiero que el dashboard cargue rápido para poder tomar decisiones sin demora.
- Como usuario, quiero que la aplicación se vea bien en celular para usarla en cualquier dispositivo.
- Como desarrollador, quiero tener pruebas automáticas para validar las funciones críticas del sistema.
- Como equipo, quiero una guía de despliegue clara para subir el proyecto a producción sin errores.
- Como administrador, quiero saber que los reports y la configuración del QR funcionan de forma estable y optimizada.

## Backlog Sprint 9

1. Optimización
   - Revisar y optimizar consultas del dashboard y los reportes de historial.
   - Asegurar que el `dashboard` no realice consultas redundantes.
   - Optimizar la generación de reportes CSV/Excel/PDF para que no bloquee el servidor.
   - Validar que las tablas con datos largos usen paginación y `table-responsive`.

2. Pruebas
   - Crear pruebas unitarias para:
     - `ConfiguracionQR.get_solo()`
     - `CodigoQR.save()` y renovación de QR.
     - vistas de `configuracion_qr`, `reporte_historial` y logout.
   - Crear pruebas de integración para el flujo:
     - login -> dashboard -> logout.
     - validación QR -> registro en `HistorialIngreso`.
   - Agregar pruebas para los exportes CSV/XLSX/PDF.

3. Responsive
   - Verificar que `templates/base.html` y `templates/usuarios/dashboard.html` respondan bien en móvil.
   - Asegurar que los cards, tablas y formularios usen clases Bootstrap responsive.
   - Probar el diseño en múltiples tamaños de pantalla y corregir desbordes.

4. Documentación
   - Actualizar `README.md` con los pasos de setup, dependencias y despliegue.
   - Documentar el uso de:
     - configuración QR
     - reportes PDF/Excel
     - validación de accesos
   - Añadir criterios de definición de done para Sprint 9.

5. Despliegue
   - Preparar recomendaciones para producción:
     - `DEBUG=False`
     - `ALLOWED_HOSTS`
     - manejo de `STATIC_ROOT` y `MEDIA_ROOT`
   - Documentar los comandos necesarios:
     - `manage.py migrate`
     - `manage.py collectstatic`
     - configuraciones de servidor WSGI / host.
   - Validar la base de datos MySQL y el uso de credenciales seguras.

## Definición de Done

- El proyecto carga correctamente y el dashboard abre en tiempos razonables.
- Las funcionalidades críticas están cubiertas por pruebas automáticas.
- La interfaz es usable en escritorio y móvil.
- `README.md` incluye guía de instalación, uso y despliegue.
- Existe un plan de despliegue documentado para producción.
- El proyecto pasa `python manage.py check`.
