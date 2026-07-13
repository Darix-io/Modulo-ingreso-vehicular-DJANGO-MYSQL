from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Ruta principal que renderiza nuestra plantilla base
    path('', TemplateView.as_view(template_name='base.html'), name='home'),
]