from django.urls import path
from .views import QrListView, renovar_qr_view, validar_acceso_view

app_name = 'qr'

urlpatterns = [
    path('', QrListView.as_view(), name='lista'),
    path('renovar/<int:pk>/', renovar_qr_view, name='renovar'),
    path('validar/', validar_acceso_view, name='validar'),
]