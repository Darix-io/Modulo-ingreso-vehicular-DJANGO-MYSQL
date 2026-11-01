from django.urls import path

from .views import (
    PropietarioActivateView,
    PropietarioCreateView,
    PropietarioDeactivateView,
    PropietarioDeleteView,
    PropietarioListView,
    PropietarioUpdateView,
)

app_name = 'propietarios'

urlpatterns = [
    path('', PropietarioListView.as_view(), name='lista'),
    path('nuevo/', PropietarioCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', PropietarioUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', PropietarioDeleteView.as_view(), name='eliminar'),
    path('activar/<int:pk>/', PropietarioActivateView.as_view(), name='activar'),
    path('desactivar/<int:pk>/', PropietarioDeactivateView.as_view(), name='desactivar'),
]
