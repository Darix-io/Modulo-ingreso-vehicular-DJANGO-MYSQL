"""
Capa de SERVICIOS de la app QR.

Aquí vive la lógica de negocio (las reglas del sistema), separada de las
vistas. Las vistas solo reciben la petición, llaman a un servicio y
muestran el resultado. Así la lógica se puede probar y reutilizar.

- generador.py     -> crea la imagen PNG del código QR
- validacion.py    -> decide si un vehículo puede entrar/salir
- estadisticas.py  -> números del panel de control (dashboard)
- reportes.py      -> exporta el historial a CSV, Excel y PDF
"""
