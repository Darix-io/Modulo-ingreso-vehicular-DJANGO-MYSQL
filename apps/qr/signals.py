"""
Señales: código que se ejecuta automáticamente cuando pasa algo en la BD.

Aquí: cuando se CREA un vehículo, se le crea su código QR.
Este archivo se carga en apps.py -> QrConfig.ready()
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.vehiculos.models import Vehiculo

from .models import CodigoQR


@receiver(post_save, sender=Vehiculo)
def crear_codigo_qr(sender, instance, created, **kwargs):
    if created:
        CodigoQR.objects.create(vehiculo=instance)
