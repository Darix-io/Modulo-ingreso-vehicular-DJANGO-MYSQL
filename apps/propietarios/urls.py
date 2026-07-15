from django.urls import path
from .views import (
    PropietarioListView,
    PropietarioCreateView,
    PropietarioUpdateView,
    PropietarioDeleteView,
    PropietarioActivateView,
    PropietarioDeactivateView,
)

app_name = 'propietarios'

urlpatterns = [
    path('', PropietarioListView.as_view(), name='lista'),
    path('nuevo/', PropietarioCreateView.as_view(), name='crear'),
    
    # Rutas dinámicas que esperan el ID (pk) del propietario
    path('editar/<int:pk>/', PropietarioUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', PropietarioDeleteView.as_view(), name='eliminar'),
    path('activar/<int:pk>/', PropietarioActivateView.as_view(), name='activar'),
    path('desactivar/<int:pk>/', PropietarioDeactivateView.as_view(), name='desactivar'),
]