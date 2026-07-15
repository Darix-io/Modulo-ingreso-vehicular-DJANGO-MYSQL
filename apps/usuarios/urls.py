from django.urls import path
from .views import CustomLoginView, DashboardView, logout_view

app_name = 'usuarios'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'), # Ruta del panel
]