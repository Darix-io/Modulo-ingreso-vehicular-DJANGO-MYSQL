"""Datos de prueba compartidos por las pruebas de movimientos, historial y reportes (Fase 7)."""
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.models import HistorialIngreso, RegistroMovimiento
from apps.usuarios.models import Rol
from apps.vehiculos.models import Vehiculo


def inicio_de_hoy():
    return timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BaseRegistrosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        rol_seguridad = Rol.objects.create(nombre=PERSONAL_SEGURIDAD)
        cls.admin = Usuario.objects.create_user(
            username='adm', email='adm@example.com', cedula='0900000001', password='Clave12345!',
            first_name='Carlos', last_name='Mendoza', rol=Rol.objects.create(nombre=ADMINISTRADOR))
        cls.victor = Usuario.objects.create_user(
            username='seguridad', email='vm@example.com', cedula='0900000002', password='Clave12345!',
            first_name='Víctor', last_name='Morán', rol=rol_seguridad)
        cls.luis = Usuario.objects.create_user(
            username='seguridad2', email='lc@example.com', cedula='0900000003', password='Clave12345!',
            first_name='Luis', last_name='Castro', rol=rol_seguridad)
        cls.ana = Propietario.objects.create(
            nombre='Ana Mora Vera', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente')
        cls.pedro = Propietario.objects.create(
            nombre='Pedro Loor Zambrano', numero_identidad='0922222222', celular='0992222222',
            correo='pedro@unemi.edu.ec', tipo='Estudiante')
        cls.hilux = Vehiculo.objects.create(
            propietario=cls.ana, placa='GSA-3841', marca='Toyota', modelo='Hilux', color='Blanco')
        cls.sail = Vehiculo.objects.create(
            propietario=cls.pedro, placa='PBA-7219', marca='Chevrolet', modelo='Sail', color='Rojo')

    # --- datos de prueba
    def movimiento(self, vehiculo, estado, tipo=RegistroMovimiento.INGRESO, detalle='', guardia=None, fecha=None):
        creado = RegistroMovimiento.objects.create(
            codigo_qr=vehiculo.codigo_qr, vehiculo=vehiculo, tipo=tipo, estado=estado,
            usuario_validador=guardia or self.victor, detalle=detalle)
        if fecha:
            RegistroMovimiento.objects.filter(pk=creado.pk).update(fecha=fecha)
        return creado

    def ingreso(self, vehiculo, fecha, guardia=None):
        creado = HistorialIngreso.objects.create(vehiculo=vehiculo, usuario_validador=guardia or self.victor)
        HistorialIngreso.objects.filter(pk=creado.pk).update(fecha_ingreso=fecha)
        return creado
