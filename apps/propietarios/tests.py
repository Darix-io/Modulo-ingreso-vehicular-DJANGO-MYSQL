from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD
from apps.qr.models import HistorialIngreso, RegistroMovimiento
from apps.usuarios.models import Rol
from apps.vehiculos.models import Vehiculo

from .filters import contadores_por_tipo, filtrar_propietarios, leer_filtros
from .forms import PropietarioForm
from .models import Propietario
from .validadores import validar_celular, validar_documento


def datos_validos(**cambios):
    datos = {
        'nombre': 'Juan Pérez Mora', 'tipo': 'Docente', 'numero_identidad': '0912345678',
        'celular': '0991234567', 'correo': 'juan@unemi.edu.ec',
    }
    datos.update(cambios)
    return datos


class ValidadoresTests(TestCase):
    def test_cedula_exactamente_10_digitos(self):
        self.assertEqual(validar_documento('0912345678', 'Estudiante'), '0912345678')
        for malo in ('091234567', '09123456789', '09123456ab', '0912 34567', ''):
            with self.assertRaises(ValidationError, msg=malo):
                validar_documento(malo, 'Docente')

    def test_visitante_puede_usar_otro_documento_de_6_a_20_caracteres(self):
        self.assertEqual(validar_documento('ab123456', 'Visitante'), 'AB123456')   # pasaporte
        self.assertEqual(validar_documento('0912345678', 'Visitante'), '0912345678')
        for malo in ('12345', 'A' * 21, 'AB 1234', 'AB-1234'):
            with self.assertRaises(ValidationError, msg=malo):
                validar_documento(malo, 'Visitante')

    def test_celular_10_digitos_que_empiecen_con_09(self):
        self.assertEqual(validar_celular('0991234567'), '0991234567')
        for malo in ('0891234567', '099123456', '09912345678', '09912345ab', '+593991234567'):
            with self.assertRaises(ValidationError, msg=malo):
                validar_celular(malo)


class PropietarioFormTests(TestCase):
    def test_datos_validos(self):
        form = PropietarioForm(datos_validos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_cedula_corta_da_error_en_su_campo(self):
        form = PropietarioForm(datos_validos(numero_identidad='12345'))
        self.assertFalse(form.is_valid())
        self.assertIn('numero_identidad', form.errors)

    def test_visitante_con_pasaporte_es_valido(self):
        form = PropietarioForm(datos_validos(tipo='Visitante', numero_identidad='pa123456'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['numero_identidad'], 'PA123456')

    def test_celular_que_no_empieza_con_09(self):
        form = PropietarioForm(datos_validos(celular='0791234567'))
        self.assertIn('celular', form.errors)

    def test_nombre_se_normaliza_y_correo_va_en_minusculas(self):
        form = PropietarioForm(datos_validos(nombre='  Ana   María  Mora ', correo='ANA@UNEMI.EDU.EC'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['nombre'], 'Ana María Mora')
        self.assertEqual(form.cleaned_data['correo'], 'ana@unemi.edu.ec')

    def test_identidad_y_correo_repetidos(self):
        Propietario.objects.create(**datos_validos())
        form = PropietarioForm(datos_validos())
        self.assertIn('numero_identidad', form.errors)
        self.assertIn('correo', form.errors)


class BasePropietariosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        cls.admin = Usuario.objects.create_user(
            username='adm', email='adm@example.com', cedula='0900000001', password='Clave12345!',
            rol=Rol.objects.create(nombre=ADMINISTRADOR))
        cls.guardia = Usuario.objects.create_user(
            username='gua', email='gua@example.com', cedula='0900000002', password='Clave12345!',
            rol=Rol.objects.create(nombre=PERSONAL_SEGURIDAD))

    def propietario(self, n, tipo='Estudiante', estado=True, nombre=None):
        return Propietario.objects.create(
            nombre=nombre or f'Persona Número{n}', tipo=tipo, estado=estado,
            numero_identidad=f'09{n:08d}', celular=f'09{n:08d}', correo=f'p{n}@unemi.edu.ec')


class ListaPropietariosTests(BasePropietariosTests):
    def setUp(self):
        self.propietario(1, 'Estudiante')
        self.propietario(2, 'Estudiante', estado=False)
        self.propietario(3, 'Docente', nombre='Roberto Álava')
        self.propietario(4, 'Visitante')

    def test_contadores_por_tipo(self):
        pestanas = {p['etiqueta']: p['cantidad'] for p in contadores_por_tipo(leer_filtros({}))}
        self.assertEqual(pestanas, {
            'Todos': 4, 'Estudiante': 2, 'Docente': 1, 'Administrativo': 0, 'Visitante': 1})

    def test_contadores_respetan_busqueda_y_estado_pero_no_el_tipo(self):
        filtros = leer_filtros({'estado': 'activo', 'tipo': 'Docente'})
        pestanas = {p['etiqueta']: p['cantidad'] for p in contadores_por_tipo(filtros)}
        self.assertEqual(pestanas['Estudiante'], 1)      # el inactivo no cuenta
        self.assertEqual(pestanas['Todos'], 3)

    def test_filtros_de_la_lista(self):
        self.assertEqual(filtrar_propietarios(leer_filtros({'tipo': 'Estudiante'})).count(), 2)
        self.assertEqual(filtrar_propietarios(leer_filtros({'estado': 'inactivo'})).count(), 1)
        self.assertEqual(filtrar_propietarios(leer_filtros({'q': 'LAVA'})).count(), 1)

    def test_pantalla_muestra_pestanas_y_datos(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('propietarios:lista'))
        self.assertContains(respuesta, 'Docente')
        self.assertContains(respuesta, 'Total: 4 registros')
        self.assertContains(respuesta, 'Roberto Álava')
        self.assertEqual(respuesta.context['total_registros'], 4)

    def test_pestana_filtra_por_tipo(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('propietarios:lista'), {'tipo': 'Docente'})
        self.assertEqual([p.nombre for p in respuesta.context['propietarios']], ['Roberto Álava'])

    def test_paginacion_conserva_los_filtros(self):
        for n in range(10, 30):
            self.propietario(n, 'Estudiante')
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('propietarios:lista'), {'tipo': 'Estudiante'})
        self.assertContains(respuesta, 'page=2')
        self.assertContains(respuesta, 'tipo=Estudiante')

    def test_administrador_ve_las_acciones(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('propietarios:lista'))
        self.assertContains(respuesta, 'Nuevo propietario')
        self.assertContains(respuesta, 'Acciones')
        self.assertContains(respuesta, '/propietarios/editar/')

    def test_seguridad_ve_la_lista_sin_botones_de_gestion(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('propietarios:lista'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Roberto Álava')
        for oculto in ('Nuevo propietario', '/propietarios/editar/', '/propietarios/eliminar/',
                       '/propietarios/desactivar/', '/propietarios/activar/'):
            self.assertNotContains(respuesta, oculto)


class PermisosYAccionesTests(BasePropietariosTests):
    def setUp(self):
        self.p = self.propietario(1)

    def test_seguridad_no_puede_crear_editar_ni_eliminar(self):
        self.client.force_login(self.guardia)
        self.assertEqual(self.client.get(reverse('propietarios:crear')).status_code, 403)
        self.assertEqual(self.client.get(reverse('propietarios:editar', args=[self.p.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('propietarios:eliminar', args=[self.p.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('propietarios:desactivar', args=[self.p.pk])).status_code, 403)
        self.assertTrue(Propietario.objects.filter(pk=self.p.pk, estado=True).exists())

    def test_activar_y_desactivar_solo_por_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('propietarios:desactivar', args=[self.p.pk])).status_code, 405)
        self.client.post(reverse('propietarios:desactivar', args=[self.p.pk]))
        self.p.refresh_from_db()
        self.assertFalse(self.p.estado)
        self.client.post(reverse('propietarios:activar', args=[self.p.pk]))
        self.p.refresh_from_db()
        self.assertTrue(self.p.estado)

    def test_crear_con_datos_validos_y_con_errores(self):
        self.client.force_login(self.admin)
        malo = self.client.post(reverse('propietarios:crear'), datos_validos(celular='123'))
        self.assertEqual(malo.status_code, 200)
        self.assertContains(malo, 'empezar con 09')
        self.assertFalse(Propietario.objects.filter(correo='juan@unemi.edu.ec').exists())

        bueno = self.client.post(reverse('propietarios:crear'), datos_validos())
        self.assertRedirects(bueno, reverse('propietarios:lista'))
        self.assertTrue(Propietario.objects.filter(correo='juan@unemi.edu.ec').exists())

    def test_formulario_muestra_modo_y_campos(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('propietarios:crear')), 'Registrar propietario')
        edicion = self.client.get(reverse('propietarios:editar', args=[self.p.pk]))
        self.assertContains(edicion, 'Modo edición')
        self.assertContains(edicion, self.p.nombre)


class EliminarPropietarioTests(BasePropietariosTests):
    def setUp(self):
        self.p = self.propietario(1, nombre='Roberto Álava')
        self.v1 = Vehiculo.objects.create(propietario=self.p, placa='GSA-3841', marca='Toyota', modelo='Hilux', color='Blanco')
        self.v2 = Vehiculo.objects.create(propietario=self.p, placa='PBA-7219', marca='Chevrolet', modelo='Aveo', color='Rojo')
        HistorialIngreso.objects.create(vehiculo=self.v1)
        RegistroMovimiento.objects.create(
            codigo_qr=self.v1.codigo_qr, vehiculo=self.v1, estado=RegistroMovimiento.AUTORIZADO)
        RegistroMovimiento.objects.create(
            codigo_qr=self.v2.codigo_qr, vehiculo=self.v2, estado=RegistroMovimiento.DENEGADO, detalle='Código expirado')

    def test_confirmacion_muestra_lo_que_se_borra_de_verdad(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('propietarios:eliminar', args=[self.p.pk]))
        resumen = respuesta.context['resumen']
        self.assertEqual(resumen['total_vehiculos'], 2)
        self.assertEqual(resumen['total_qr'], 2)
        self.assertEqual(resumen['total_ingresos'], 1)
        self.assertEqual(resumen['total_movimientos'], 2)
        self.assertContains(respuesta, 'GSA-3841')
        self.assertContains(respuesta, 'PBA-7219')
        self.assertContains(respuesta, 'irreversible')

    def test_sin_marcar_la_confirmacion_no_se_elimina(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('propietarios:eliminar', args=[self.p.pk]))
        self.assertRedirects(respuesta, reverse('propietarios:eliminar', args=[self.p.pk]))
        self.assertTrue(Propietario.objects.filter(pk=self.p.pk).exists())

    def test_con_confirmacion_se_elimina_en_cascada(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('propietarios:eliminar', args=[self.p.pk]), {'confirmo': 'on'})
        self.assertRedirects(respuesta, reverse('propietarios:lista'))
        self.assertFalse(Propietario.objects.filter(pk=self.p.pk).exists())
        self.assertEqual(Vehiculo.objects.count(), 0)
        self.assertEqual(RegistroMovimiento.objects.count(), 0)
        self.assertEqual(HistorialIngreso.objects.count(), 0)
