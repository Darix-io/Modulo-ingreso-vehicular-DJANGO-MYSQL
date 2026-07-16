from django.urls import path
from django.shortcuts import redirect
from .views import CustomLoginView, DashboardView, logout_view

app_name = 'usuarios'


def root_view(request):
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')
    return redirect('usuarios:login')


urlpatterns = [
    path('', root_view, name='root'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'), # Ruta del panel
]