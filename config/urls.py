from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')), 
    path('propietarios/', include('apps.propietarios.urls')),
    path('vehiculos/', include('apps.vehiculos.urls')), # <-- Nueva línea agregada
]