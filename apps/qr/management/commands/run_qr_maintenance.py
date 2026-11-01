"""
Mantenimiento de códigos QR.

    python manage.py run_qr_maintenance            -> solo marca como inactivos los expirados
    python manage.py run_qr_maintenance --renovar  -> además renueva los de vehículos autorizados

Antes este comando expiraba TODOS los QR y luego los renovaba TODOS, así que
la expiración no servía de nada (incluso reactivaba vehículos suspendidos).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.qr.models import CodigoQR
from apps.vehiculos.models import Vehiculo


class Command(BaseCommand):
    help = 'Expira los códigos QR vencidos y, opcionalmente, renueva los de vehículos autorizados.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--renovar',
            action='store_true',
            help='Renovar los QR vencidos de vehículos autorizados con propietario activo.',
        )

    def handle(self, *args, **options):
        ahora = timezone.now()
        expirados = CodigoQR.objects.filter(activo=True, fecha_expiracion__lte=ahora).update(activo=False)
        self.stdout.write(self.style.SUCCESS(f'{expirados} códigos QR marcados como expirados.'))

        if not options['renovar']:
            return

        renovables = CodigoQR.objects.select_related('vehiculo').filter(
            fecha_expiracion__lte=ahora,
            vehiculo__estado=Vehiculo.AUTORIZADO,
            vehiculo__propietario__estado=True,
        )
        renovados = 0
        for codigo_qr in renovables:
            codigo_qr.renovar()
            renovados += 1
        self.stdout.write(self.style.SUCCESS(f'{renovados} códigos QR renovados.'))
