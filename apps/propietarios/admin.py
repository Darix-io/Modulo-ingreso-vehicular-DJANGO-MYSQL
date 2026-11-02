from django.contrib import admin
from .models import Propietario

@admin.register(Propietario)
class PropietarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero_identidad', 'tipo', 'celular', 'estado')
    search_fields = ('nombre', 'numero_identidad', 'correo')
    list_filter = ('tipo', 'estado')