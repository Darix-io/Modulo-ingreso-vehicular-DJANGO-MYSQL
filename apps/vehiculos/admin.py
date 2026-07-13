from django.contrib import admin
from .models import Vehiculo

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'propietario', 'estado')
    search_fields = ('placa', 'propietario__nombre', 'propietario__numero_identidad')
    list_filter = ('estado', 'marca')
    