from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.qr.models import CodigoQR


class Command(BaseCommand):
    help = 'Marca como inactivos los códigos QR que hayan expirado.'

    def handle(self, *args, **options):
        ahora = timezone.now()
        qrs = CodigoQR.objects.filter(activo=True, fecha_expiracion__lte=ahora)
        cont = qrs.update(activo=False)
        self.stdout.write(self.style.SUCCESS(f'{cont} códigos QR expirados.'))
