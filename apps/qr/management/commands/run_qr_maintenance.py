"""
Mantenimiento de códigos QR.

    python manage.py run_qr_maintenance            -> marca como inactivos los expirados y, si la
                                                      «Renovación automática» está activada en
                                                      Configuración QR, renueva los de vehículos autorizados
    python manage.py run_qr_maintenance --renovar  -> renueva aunque la configuración la tenga desactivada

Antes este comando expiraba TODOS los QR y luego los renovaba TODOS, así que
la expiración no servía de nada (incluso reactivaba vehículos suspendidos).
La lógica está en apps/qr/services/mantenimiento.py.
"""
from django.core.management.base import BaseCommand

from apps.qr.services.mantenimiento import ejecutar_mantenimiento


class Command(BaseCommand):
    help = 'Expira los códigos QR vencidos y renueva los de vehículos autorizados si la renovación automática está activada.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--renovar',
            action='store_true',
            help='Renovar los QR vencidos de vehículos autorizados con propietario activo, aunque la configuración no lo pida.',
        )

    def handle(self, *args, **options):
        expirados, renovados, se_renovo = ejecutar_mantenimiento(forzar_renovacion=options['renovar'])
        self.stdout.write(self.style.SUCCESS(f'{expirados} códigos QR marcados como expirados.'))
        if se_renovo:
            self.stdout.write(self.style.SUCCESS(f'{renovados} códigos QR renovados.'))
        else:
            self.stdout.write('Renovación automática desactivada: no se renovó ningún código.')
