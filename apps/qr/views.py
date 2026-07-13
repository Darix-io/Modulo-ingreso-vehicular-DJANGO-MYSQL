from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render
from django.utils import timezone
from .models import CodigoQR

class QrListView(LoginRequiredMixin, ListView):
    model = CodigoQR
    template_name = 'qr/qr_list.html'
    context_object_name = 'qrs'

def renovar_qr_view(request, pk):
    qr = get_object_or_404(CodigoQR, pk=pk)
    qr.renovar()
    messages.success(request, 'Código QR renovado con éxito.')
    return redirect('qr:lista')

def validar_acceso_view(request):
    token = request.GET.get('token') # Recibimos el UUID por la URL
    resultado = None
    
    if token:
        try:
            # Buscamos el QR por el contenido (UUID)
            qr = CodigoQR.objects.get(contenido=token)
            
            # Validamos reglas de negocio
            if qr.activo and qr.fecha_expiracion > timezone.now():
                resultado = {
                    'status': 'success',
                    'mensaje': 'Acceso Autorizado',
                    'vehiculo': qr.vehiculo
                }
            else:
                resultado = {
                    'status': 'danger',
                    'mensaje': 'Código expirado o desactivado',
                }
        except CodigoQR.DoesNotExist:
            resultado = {
                'status': 'danger',
                'mensaje': 'Código QR no válido',
            }
            
    return render(request, 'qr/validar.html', {'resultado': resultado})