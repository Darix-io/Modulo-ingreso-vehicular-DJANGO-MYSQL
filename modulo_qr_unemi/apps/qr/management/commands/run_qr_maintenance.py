from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.qr.models import CodigoQR


class Command(BaseCommand):
    help = 'Ejecuta el ciclo de mantenimiento de códigos QR: expira y renueva según sea necesario.'

    def handle(self, *args, **options):
        ahora = timezone.now()
        expirados = CodigoQR.objects.filter(activo=True, fecha_expiracion__lte=ahora)
        expirados_count = expirados.update(activo=False)

        renovados = 0
        for qr in CodigoQR.objects.filter(fecha_expiracion__lte=ahora):
            qr.renovar()
            renovados += 1

        self.stdout.write(self.style.SUCCESS(f'Proceso de mantenimiento QR completado.'))
        self.stdout.write(self.style.SUCCESS(f'  - {expirados_count} códigos expirados.'))
        self.stdout.write(self.style.SUCCESS(f'  - {renovados} códigos renovados.'))
