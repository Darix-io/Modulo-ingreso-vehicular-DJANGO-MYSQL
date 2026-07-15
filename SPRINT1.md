# Sprint 1 - Implementación funcional

## Objetivo

Completar la primera versión funcional del sistema de control de ingreso vehicular.

## Entregables

- Conexión a MySQL verificada y migraciones aplicadas.
- Login y roles de usuario funcionando en la aplicación.
- Registro y gestión de propietarios.
- Registro y gestión de vehículos.
- Generación de códigos QR válidos para vehículos.
- Validación de acceso a través del QR y registro de ingresos.
- Dashboard con métricas reales de uso.

## Backlog Sprint 1

1. Configurar y verificar MySQL real
   - Confirmar que la base de datos `db_control_acceso` existe.
   - Instalar el driver de MySQL necesario (`mysqlclient` o `PyMySQL`).
   - Probar `python manage.py migrate` con MySQL.
   - Asegurar que Django usa MySQL en producción y/o desarrollo.

2. Asegurar login y usuarios
   - Confirmar que el `AUTH_USER_MODEL` `usuarios.Usuario` funciona sin errores.
   - Probar login, logout y redirección al dashboard.
   - Validar permisos básicos y acceso a las páginas de gestión.

3. Validación de QR y control de acceso
   - Verificar que el QR generado incluye el token o URL de validación.
   - Probar el formulario de validación con token directo y con enlace.
   - Asegurar que `HistorialIngreso` se registra correctamente.
   - Confirmar que el dashboard `Ingresos hoy` muestra números reales.

4. Gestión de propietarios y vehículos
   - Validar formularios de creación/edición/eliminación de propietarios.
   - Validar formularios de creación/edición/eliminación de vehículos.
   - Confirmar que cada vehículo puede generar y renovar QR.

5. Mejoras de interfaz y usabilidad
   - Validar que Bootstrap funciona en todas las vistas principales.
   - Asegurar que el dashboard muestra datos legibles.
   - Ajustar plantillas si hace falta para el flujo de acceso.

## Definición de Done

- El proyecto corre en MySQL sin usar SQLite.
- El login básico está operativo.
- Se puede crear un vehículo y generar su QR.
- La validación de un token registra un ingreso en `HistorialIngreso`.
- El dashboard muestra `Ingresos hoy` correctamente.
- La aplicación no arroja errores críticos en `python manage.py check`.
