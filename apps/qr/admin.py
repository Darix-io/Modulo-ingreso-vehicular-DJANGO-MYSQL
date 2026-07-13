from django.contrib import admin
from .models import CodigoQR

@admin.register(CodigoQR)
class CodigoQRAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha_creacion', 'fecha_expiracion', 'activo')
    readonly_fields = ('contenido', 'imagen') # No dejamos que el admin modifique estos campos a mano