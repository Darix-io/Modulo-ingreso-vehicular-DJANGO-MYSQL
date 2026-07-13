from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <-- Importamos settings
from django.conf.urls.static import static # <-- Importamos static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')), 
    path('propietarios/', include('apps.propietarios.urls')),
    path('vehiculos/', include('apps.vehiculos.urls')),
    path('qr/', include('apps.qr.urls')),
]

# Esta condición añade la ruta para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)