from django.urls import path
from django.contrib.auth.views import LogoutView # Importamos LogoutView
from .views import CustomLoginView, DashboardView

app_name = 'usuarios'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), # Ruta de salida
    path('dashboard/', DashboardView.as_view(), name='dashboard'), # Ruta del panel
]