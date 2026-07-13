from django.urls import path
from .views import VehiculoListView, VehiculoCreateView, VehiculoUpdateView, VehiculoDeleteView

app_name = 'vehiculos'

urlpatterns = [
    path('', VehiculoListView.as_view(), name='lista'),
    path('nuevo/', VehiculoCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', VehiculoUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', VehiculoDeleteView.as_view(), name='eliminar'),
]