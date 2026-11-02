from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol

# Registramos el modelo Rol de forma estándar
admin.site.register(Rol)

# Configuramos cómo se verá nuestro Usuario personalizado en el panel
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Columnas que veremos en la lista de usuarios
    list_display = ('email', 'first_name', 'last_name', 'cedula', 'rol', 'is_active')
    
    # Campos por los que podremos buscar
    search_fields = ('email', 'cedula', 'first_name', 'last_name')
    
    # Ordenamiento por defecto
    ordering = ('email',)
    
    # Agregamos nuestros campos personalizados al formulario de edición de Django
    fieldsets = UserAdmin.fieldsets + (
        ('Información Institucional', {'fields': ('cedula', 'rol')}),
    )
    
    # Agregamos nuestros campos al formulario de creación de nuevos usuarios desde el admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Institucional', {'fields': ('cedula', 'rol')}),
    )