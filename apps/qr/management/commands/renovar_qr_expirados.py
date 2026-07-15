from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.qr.models import CodigoQR


class Command(BaseCommand):
    help = 'Renueva automáticamente los códigos QR expirados y los marca como activos.'

    def handle(self, *args, **options):
        expirados = CodigoQR.objects.filter(fecha_expiracion__lte=timezone.now())
        contador = 0
        for qr in expirados:
            qr.renovar()
            contador += 1
        self.stdout.write(self.style.SUCCESS(f'{contador} códigos QR renovados automáticamente.'))
