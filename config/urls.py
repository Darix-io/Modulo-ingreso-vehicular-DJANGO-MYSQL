from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import HomeRedirectView, previsualizar_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeRedirectView.as_view(), name='home'),
    path('', include('apps.usuarios.urls')),
    path('propietarios/', include('apps.propietarios.urls')),
    path('vehiculos/', include('apps.vehiculos.urls')),
    path('qr/', include('apps.qr.urls')),
]

# En desarrollo, Django sirve las imágenes QR guardadas en /media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Vista previa de las páginas de error: /errores/403/, /errores/404/ y /errores/500/
    urlpatterns += [path('errores/<int:codigo>/', previsualizar_error, name='previsualizar_error')]
