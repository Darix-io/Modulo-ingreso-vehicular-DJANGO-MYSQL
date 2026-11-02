"""
Corrige los movimientos guardados con el texto antiguo «Vehículo acceso suspendido»
(salía de get_estado_display()). El motivo correcto es «Vehículo suspendido».
"""
from django.db import migrations

TEXTO_ANTIGUO = 'Vehículo acceso suspendido'
TEXTO_CORRECTO = 'Vehículo suspendido'


def corregir_motivo(apps, schema_editor):
    RegistroMovimiento = apps.get_model('qr', 'RegistroMovimiento')
    RegistroMovimiento.objects.filter(detalle=TEXTO_ANTIGUO).update(detalle=TEXTO_CORRECTO)


class Migration(migrations.Migration):

    dependencies = [
        ('qr', '0004_configuracionqr'),
    ]

    operations = [
        # No se deshace: volver al texto antiguo no tiene sentido
        migrations.RunPython(corregir_motivo, migrations.RunPython.noop),
    ]
