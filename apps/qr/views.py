from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
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