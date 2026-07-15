from django.contrib import admin
from .models import ConfiguracionQR, CodigoQR, HistorialIngreso, RegistroMovimiento

@admin.register(ConfiguracionQR)
class ConfiguracionQRAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'expiration_days', 'activar_qr', 'permitir_reutilizacion', 'ultima_actualizacion')
    readonly_fields = ('ultima_actualizacion',)

@admin.register(CodigoQR)
class CodigoQRAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha_creacion', 'fecha_expiracion', 'activo')
    readonly_fields = ('contenido', 'imagen')

@admin.register(HistorialIngreso)
class HistorialIngresoAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha_ingreso', 'usuario_validador')
    list_filter = ('fecha_ingreso',)

@admin.register(RegistroMovimiento)
class RegistroMovimientoAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'codigo_qr', 'tipo', 'estado', 'usuario_validador', 'fecha')
    list_filter = ('tipo', 'estado', 'fecha')
    search_fields = ('vehiculo__placa', 'codigo_qr__contenido', 'usuario_validador__username')
