# Instrucciones de diseño — GaritaQR (Etapa B)

Este documento explica cómo aplicar el diseño creado en Stitch a las plantillas
Django del proyecto. Léelo completo antes de empezar y síguelo en cada fase.

- Las pantallas de referencia están en la carpeta `diseno-stitch/`: archivos HTML exportados y capturas.
- Las reglas de arquitectura del proyecto están en `CLAUDE.md` y `README.md`. Siguen vigentes.
- La usuaria es principiante: explica cada cambio en español antes de hacerlo.

---

## 1. Reglas generales (obligatorias)

1. **El diseño de Stitch es una referencia visual, no código para copiar tal cual.**
   Toma la estructura, los colores, la tipografía y los componentes, pero muestra
   **solo datos reales** que existen en los modelos y las vistas.
2. **No inventes funciones.** Si una pantalla de Stitch muestra algo que el sistema no
   tiene y que no está en la lista de mejoras (sección 5), omítelo.
3. **Conserva todo lo de Django:** `{% extends %}`, `{% block %}`, `{% url %}` con los
   nombres de ruta actuales, `{% csrf_token %}`, `{{ form }}`, mensajes, paginación
   (`page_obj`) y los nombres de variables de contexto que ya usan las vistas.
4. **No cambies nombres de URL, modelos ni tablas.**
5. Las acciones que cambian datos (activar, desactivar, renovar, eliminar) siguen
   siendo formularios **POST** con `{% csrf_token %}`. Nunca con enlaces `<a href>`.
6. **Permisos por rol en las plantillas:** el menú "Configuración QR" y los botones de
   crear, editar o eliminar propietarios y vehículos solo se muestran si
   `user.is_administrador` es verdadero. El Personal de Seguridad no los ve.
7. Todo el texto de la interfaz va en **español**.
8. Al terminar cada fase: ejecutar `python manage.py check` y `python manage.py test`,
   corregir lo que falle, explicar los cambios a la usuaria y hacer **un commit por fase**.
9. Después de cada fase, **detente y espera** a que la usuaria revise en el navegador
   y escriba "continúa con la fase N".

---

## 2. Design system

**Stack de estilos:** Tailwind CSS cargado por CDN en `base.html`, con la configuración
de colores y fuentes de abajo. Eliminar Bootstrap del proyecto y adaptar las clases
de los widgets de formularios (`forms.py`) a Tailwind, o definir en `static/css/style.css`
estilos equivalentes para `.form-control` y `.form-select`. Elegir una sola opción
y aplicarla en todo el proyecto.

**Colores:**

| Token | Hex | Uso |
|---|---|---|
| primary | `#0A2540` | Menú activo, botones principales, encabezados de tabla oscuros |
| secondary | `#F59E0B` | Acento: logo, botón "Acceso rápido a escáner", alertas de vencimiento |
| tertiary | `#1E3A8A` | Enlaces, detalles secundarios |
| neutral | `#0F172A` | Texto principal |
| fondo | `#F5F7FB` aprox. | Fondo de página (gris azulado muy claro) |

**Colores semánticos:** verde = Autorizado / Activo / Vigente, rojo = Denegado /
Suspendido / Expirado, gris = No autorizado / Inactivo, ámbar = Por vencer (3 días o menos).

**Tipografía (Google Fonts):**
- Títulos: **Hanken Grotesk**
- Texto: **Inter**
- Datos, placas, fechas, códigos y etiquetas: **JetBrains Mono**

**Íconos:** usar una sola librería en todo el proyecto. Preferir la misma que usa la
exportación de Stitch (normalmente Material Symbols).

**Componentes recurrentes:**
- **Placa ecuatoriana:** recuadro blanco con franja superior azul marino que dice
  "ECUADOR" y la placa en JetBrains Mono. Crear un *include* reutilizable:
  `templates/includes/placa.html`.
- **Badges de estado:** píldoras de color según los colores semánticos. Crear un include:
  `templates/includes/badge_estado.html`.
- **Avatar con iniciales:** círculo con las iniciales del nombre. Sin fotos.
- **Tarjetas de métricas:** título en mayúsculas pequeñas, número grande y texto de apoyo.
- **Mensajes (toasts):** los `messages` de Django se muestran como toast arriba a la
  derecha y se cierran solos.

**Logo:** el cuadrado naranja con ícono QR y el texto "Garita**QR**", como en la pantalla
de login. Usar **el mismo logo en todas las pantallas** (Stitch lo cambia entre pantallas;
ignorar las otras variantes). Crear también un favicon SVG con ese logo en `static/`.

---

## 3. Estructura común (base.html)

- **Menú lateral izquierdo** con secciones:
  - OPERACIÓN: Panel de control, Validar acceso (con badge "EN VIVO"), Movimientos
  - GESTIÓN: Propietarios, Vehículos, Códigos QR
  - AUDITORÍA: Historial, Reportes
  - SISTEMA: Configuración QR (badge "ADMIN", solo administradores)
  - Abajo: tarjeta del usuario con iniciales, nombre completo, rol y botón de cerrar sesión.
  - El ítem activo se resalta según la URL actual.
  - Corregir la alineación: todos los textos del menú alineados a la izquierda
    (en Stitch "Panel de control" aparece a la derecha).
- **Barra superior:** buscador global por placa (envía a `vehiculos:lista?q=...`),
  indicador "Sistema activo" y la **fecha actual real** con `{% now %}`.
  Omitir la campana de notificaciones y el botón de tema claro/oscuro.
- **Responsive:** en móvil el menú se oculta y se abre con un botón.

---

## 4. Qué omitir de cada pantalla de Stitch

| Pantalla | Omitir (no existe en el sistema) |
|---|---|
| Todas | Varias garitas, puestos, carriles, turnos, pluma o barrera, IoT, RFID, OCR, biometría, telemetría, hashes, firmas criptográficas, "Directorio Activo", SGA, ANT, facultades y carreras, fotos de perfil |
| Login | "¿Olvidaste tu contraseña?" y la frase "apertura de barreras" |
| Panel de control | Selector de fecha superior, autos vs. motos, estado de puestos de garita |
| Códigos QR | Botón "Generar código QR" (el QR se crea solo al registrar el vehículo), métrica "Renovaciones del mes", texto de firma criptográfica |
| Detalle QR | Tipo de vehículo, combustible, tag físico, zona del campus, facultad, "última renovación", "política institucional" |
| Configuración QR | Panel "Estado del motor" (latencia, algoritmo, biometría, sincronización) |
| Validar acceso (escritorio) | Datos técnicos de la cámara, selector Ingreso/Salida (el sistema lo alterna solo), botón "Comprobante", atajos de teclado |
| Resultados (móvil) | "Carril 01", "Sanciones de tránsito", "Matrícula vinculada", "Registrar incidencia" |
| Historial | Columna de estado Autorizado/Denegado y contadores de denegados: el historial solo contiene **ingresos autorizados** (modelo `HistorialIngreso`). Los denegados se ven en Movimientos. |
| Movimientos | Textos de detalle largos inventados. Mostrar el `detalle` real del movimiento (por ejemplo "Código expirado"). |
| Reportes | Columnas Tipo y Estado (el reporte se basa en `HistorialIngreso`, que solo tiene ingresos autorizados) |
| Vehículos | Tipo de vehículo, provincia en la placa, RUC, garita frecuente |

---

## 5. Mejoras que SÍ se deben programar

Cada mejora debe respetar la arquitectura por capas (lógica en `services/` o en el
modelo, no en la vista) y llevar su test.

1. **Validación manual por placa** (respaldo cuando el QR está dañado).
   - En `apps/qr/services/validacion.py` agregar `validar_por_placa(placa, usuario)`:
     normaliza la placa (mayúsculas, sin espacios), busca el vehículo y aplica
     **exactamente las mismas reglas** que `validar_acceso`, reutilizando
     `motivo_de_rechazo`. Si la placa no existe, devuelve "Placa no registrada".
     El `detalle` del movimiento indica "Validación manual por placa".
   - `ValidarAccesoView` acepta `?token=...` o `?placa=...`.
2. **Escáner con cámara** en la pantalla Validar acceso, usando la librería
   `html5-qrcode` por CDN con versión fija. Al leer un QR, redirige a
   `?token=<texto leído>` (la función `extraer_token` ya acepta la URL completa).
   Mantener el campo manual como respaldo. Nota: la cámara funciona en `localhost`
   o con HTTPS.
3. **Credencial QR imprimible:** nueva vista y ruta `qr:credencial` (`/qr/credencial/<pk>/`),
   con una plantilla limpia para imprimir: logo, QR grande, placa, titular, fecha de
   vencimiento y el texto "Colocar en el parabrisas". Incluye un botón "Imprimir"
   (`window.print()`). Enlazarla desde Detalle QR.
4. **Resumen de accesos del vehículo** en Detalle QR: último ingreso autorizado
   (fecha, hora y guardia) y total de ingresos del mes en curso. Calcularlo en un
   servicio, no en la plantilla.
5. **Validaciones más estrictas** en `PropietarioForm`: cédula de exactamente 10 dígitos
   (excepto si el tipo es Visitante, que puede usar otro documento de 6 a 20 caracteres)
   y celular de 10 dígitos que empiece con `09`.
6. **Contadores en las listas:**
   - Propietarios: pestañas Todos / Estudiante / Docente / Administrativo / Visitante con su cantidad.
   - Vehículos: tarjetas Autorizados / No autorizados / Suspendidos.
   - Códigos QR: Activos, Próximos a vencer (3 días o menos), Expirados o inactivos.
   - Movimientos: total de hoy, autorizados, denegados e ingresos/salidas de hoy.
7. **"Recordarme" en el login:** si no se marca, la sesión termina al cerrar el
   navegador (`request.session.set_expiry(0)`).
8. **Botones del panel:** "Acceso rápido a escáner" lleva a `qr:validar`, y
   "Descargar reporte del día" lleva al PDF del historial filtrado por la fecha de hoy.
9. **Gráficos con Chart.js** (CDN, versión fija): en el panel usar
   `access_chart_labels`, `access_chart_autorizados` y `access_chart_denegados`;
   en reportes usar la ruta `qr:reporte_historial_datos`.
10. **Datos de demostración:** crear el comando `python manage.py seed_demo`, que genere
    datos realistas de Ecuador (unos 15 propietarios de los 4 tipos, unos 20 vehículos
    con placas como GSA-3841, algunos suspendidos o no autorizados, algunos QR por vencer
    o expirados, y movimientos e ingresos repartidos en los últimos 30 días con distintos
    guardias). Como `fecha`, `fecha_ingreso` y `fecha_creacion` usan `auto_now_add`,
    ajustarlas después de crear los registros con `.update()`. El comando no debe
    duplicar datos si se ejecuta dos veces.

---

## 6. Fases de trabajo

Hacer **una fase a la vez**, con su commit, y esperar la revisión de la usuaria.

| Fase | Contenido | Archivo de referencia en `diseno-stitch/` |
|---|---|---|
| 1 | Design system, `base.html` (menú y barra superior), includes, favicon, mensajes toast, Login + "Recordarme" | login, dashboard (solo la estructura) |
| 2 | Panel de control con Chart.js | dashboard |
| 3 | Propietarios: lista con contadores, formulario, confirmación de eliminación con estilo de modal, validaciones nuevas | propietarios, propietario-form, eliminar-modal |
| 4 | Vehículos: lista con contadores, formulario con vista previa de placa, confirmación de eliminación | vehiculos |
| 5 | Códigos QR: lista con contadores, Detalle QR con resumen de accesos, credencial imprimible | codigos-qr, detalle-qr |
| 6 | Validar acceso: escritorio y móvil (responsive), cámara, validación por placa, resultados autorizado y denegado | validar-escritorio, validar-movil, resultado-autorizado, resultado-denegado |
| 7 | Movimientos con contadores, Historial, Reportes con Chart.js | movimientos, historial, reportes |
| 8 | Configuración QR | configuracion-qr |
| 9 | Comando `seed_demo`, revisión visual completa, actualizar README.md y CLAUDE.md | — |

---

## 7. Lista de verificación al final de cada fase

- [ ] `python manage.py check` sin errores
- [ ] `python manage.py test` en OK (con los tests nuevos de la fase)
- [ ] La pantalla se ve bien en escritorio y en móvil (ancho de unos 400 px)
- [ ] Solo muestra datos reales; nada de la sección 4
- [ ] Los botones de administrador están ocultos para Personal de Seguridad
- [ ] Commit hecho con un mensaje claro, por ejemplo: `Fase 3: rediseño de propietarios`
