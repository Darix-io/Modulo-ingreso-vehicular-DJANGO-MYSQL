from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
import tempfile

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.models import CodigoQR, HistorialIngreso, RegistroMovimiento
from apps.usuarios.models import Rol

from .filters import contadores_por_estado, filtrar_vehiculos, leer_filtros
from .forms import VehiculoForm
from .models import Vehiculo
from .services import resumen_eliminacion


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BaseVehiculosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        cls.admin = Usuario.objects.create_user(
            username='adm', email='adm@example.com', cedula='0900000001', password='Clave12345!',
            rol=Rol.objects.create(nombre=ADMINISTRADOR))
        cls.guardia = Usuario.objects.create_user(
            username='gua', email='gua@example.com', cedula='0900000002', password='Clave12345!',
            rol=Rol.objects.create(nombre=PERSONAL_SEGURIDAD))
        cls.activo = Propietario.objects.create(
            nombre='Ana Mora Vera', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente')
        cls.inactivo = Propietario.objects.create(
            nombre='Beto Inactivo', numero_identidad='0912345679', celular='0991234568',
            correo='beto@unemi.edu.ec', tipo='Visitante', estado=False)

    def vehiculo(self, placa, estado=Vehiculo.AUTORIZADO, propietario=None, marca='Kia'):
        return Vehiculo.objects.create(
            propietario=propietario or self.activo, placa=placa, marca=marca, modelo='Rio',
            color='Gris', estado=estado)

    def datos(self, **cambios):
        datos = {
            'propietario': self.activo.pk, 'placa': 'gsa-3841', 'marca': 'Toyota', 'modelo': 'Hilux',
            'color': 'Blanco', 'anio': 2021, 'estado': Vehiculo.AUTORIZADO, 'observaciones': '',
        }
        datos.update(cambios)
        return datos


class FormularioVehiculoTests(BaseVehiculosTests):
    def test_solo_aparecen_propietarios_activos(self):
        form = VehiculoForm()
        self.assertEqual(list(form.fields['propietario'].queryset), [self.activo])

    def test_un_propietario_inactivo_se_rechaza(self):
        form = VehiculoForm(self.datos(propietario=self.inactivo.pk))
        self.assertFalse(form.is_valid())
        self.assertIn('propietario', form.errors)

    def test_al_editar_se_conserva_el_propietario_actual_aunque_este_inactivo(self):
        v = self.vehiculo('GAA-1111', propietario=self.inactivo)
        form = VehiculoForm(instance=v)
        self.assertIn(self.inactivo, form.fields['propietario'].queryset)
        self.assertIn(self.activo, form.fields['propietario'].queryset)

    def test_el_selector_muestra_nombre_cedula_y_tipo(self):
        etiqueta = VehiculoForm().fields['propietario'].label_from_instance(self.activo)
        self.assertEqual(etiqueta, 'Ana Mora Vera · 0912345678 (Docente)')

    def test_la_placa_se_guarda_en_mayusculas_y_valida_caracteres(self):
        form = VehiculoForm(self.datos(placa=' gsa-3841 '))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['placa'], 'GSA-3841')
        self.assertIn('placa', VehiculoForm(self.datos(placa='GSA 3841!')).errors)

    def test_placa_repetida_y_anio_fuera_de_rango(self):
        self.vehiculo('GSA-3841')
        self.assertIn('placa', VehiculoForm(self.datos()).errors)
        self.assertIn('anio', VehiculoForm(self.datos(placa='GBB-0001', anio=1850)).errors)


class ContadoresYFiltrosTests(BaseVehiculosTests):
    def setUp(self):
        self.vehiculo('GAA-1111')
        self.vehiculo('GAA-2222')
        self.vehiculo('GBB-3333', Vehiculo.NO_AUTORIZADO, marca='Ford')
        self.vehiculo('GCC-4444', Vehiculo.SUSPENDIDO)

    def cantidades(self, params):
        return {c['clave']: c['cantidad'] for c in contadores_por_estado(leer_filtros(params))}

    def test_contadores_por_estado(self):
        self.assertEqual(self.cantidades({}), {'autorizado': 2, 'no_autorizado': 1, 'suspendido': 1})

    def test_contadores_respetan_la_busqueda_pero_no_el_estado(self):
        self.assertEqual(self.cantidades({'q': 'Ford', 'estado': 'autorizado'}),
                         {'autorizado': 0, 'no_autorizado': 1, 'suspendido': 0})

    def test_filtros(self):
        self.assertEqual(filtrar_vehiculos(leer_filtros({'estado': 'suspendido'})).count(), 1)
        self.assertEqual(filtrar_vehiculos(leer_filtros({'q': 'gaa'})).count(), 2)
        self.assertEqual(filtrar_vehiculos(leer_filtros({'q': 'Ana Mora'})).count(), 4)
        self.assertEqual(filtrar_vehiculos(leer_filtros({'estado': 'inventado'})).count(), 4)

    def test_pantalla_muestra_tarjetas_y_placas(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:lista'))
        self.assertContains(respuesta, 'Autorizados')
        self.assertContains(respuesta, 'No autorizados')
        self.assertContains(respuesta, 'Suspendidos')
        self.assertContains(respuesta, 'Ecuador')           # placa estilo ecuatoriano
        self.assertContains(respuesta, 'GAA-1111')
        self.assertEqual(
            {c['clave']: c['cantidad'] for c in respuesta.context['contadores']},
            {'autorizado': 2, 'no_autorizado': 1, 'suspendido': 1})

    def test_buscador_de_la_barra_superior_por_placa(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('vehiculos:lista'), {'q': 'GCC'})
        self.assertEqual([v.placa for v in respuesta.context['vehiculos']], ['GCC-4444'])

    def test_paginacion_conserva_filtros(self):
        for n in range(10, 30):
            self.vehiculo(f'GZZ-{n:04d}')
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:lista'), {'estado': 'autorizado'})
        self.assertContains(respuesta, 'page=2')
        self.assertContains(respuesta, 'estado=autorizado')

    def test_propietario_inactivo_se_senala_en_la_lista(self):
        self.vehiculo('GDD-5555', propietario=self.inactivo)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('vehiculos:lista')), 'Propietario inactivo')


class PermisosVehiculosTests(BaseVehiculosTests):
    def setUp(self):
        self.v = self.vehiculo('GAA-1111')

    def test_administrador_ve_crear_editar_y_eliminar(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:lista'))
        for visible in ('Registrar vehículo', '/vehiculos/editar/', '/vehiculos/eliminar/'):
            self.assertContains(respuesta, visible)

    def test_seguridad_ve_la_lista_sin_crear_editar_ni_eliminar(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('vehiculos:lista'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'GAA-1111')
        self.assertContains(respuesta, '/qr/detalle/')        # sí puede ver el QR
        for oculto in ('Registrar vehículo', '/vehiculos/editar/', '/vehiculos/eliminar/', '/vehiculos/nuevo/',
                       '/vehiculos/activar/', '/vehiculos/desactivar/'):
            self.assertNotContains(respuesta, oculto)

    def test_seguridad_recibe_403_al_intentar_crear_editar_o_eliminar(self):
        self.client.force_login(self.guardia)
        self.assertEqual(self.client.get(reverse('vehiculos:crear')).status_code, 403)
        self.assertEqual(self.client.post(reverse('vehiculos:crear'), self.datos(placa='GNN-0001')).status_code, 403)
        self.assertEqual(self.client.get(reverse('vehiculos:editar', args=[self.v.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('vehiculos:eliminar', args=[self.v.pk]), {'confirmo': 'on'}).status_code, 403)
        self.assertTrue(Vehiculo.objects.filter(pk=self.v.pk).exists())
        self.assertFalse(Vehiculo.objects.filter(placa='GNN-0001').exists())

    def test_seguridad_no_puede_autorizar_ni_quitar_la_autorizacion(self):
        sospechoso = self.vehiculo('GBB-2222', Vehiculo.NO_AUTORIZADO)
        self.client.force_login(self.guardia)
        self.assertEqual(self.client.post(reverse('vehiculos:activar', args=[sospechoso.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('vehiculos:desactivar', args=[self.v.pk])).status_code, 403)
        sospechoso.refresh_from_db()
        self.v.refresh_from_db()
        self.assertEqual(sospechoso.estado, Vehiculo.NO_AUTORIZADO)    # sigue igual
        self.assertEqual(self.v.estado, Vehiculo.AUTORIZADO)           # sigue igual

    def test_administrador_ve_los_botones_de_autorizacion(self):
        self.vehiculo('GBB-2222', Vehiculo.SUSPENDIDO)
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:lista'))
        self.assertContains(respuesta, '/vehiculos/activar/')
        self.assertContains(respuesta, '/vehiculos/desactivar/')

    def test_activar_y_desactivar_solo_por_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('vehiculos:desactivar', args=[self.v.pk])).status_code, 405)
        self.client.post(reverse('vehiculos:desactivar', args=[self.v.pk]))
        self.v.refresh_from_db()
        self.assertEqual(self.v.estado, Vehiculo.NO_AUTORIZADO)
        self.client.post(reverse('vehiculos:activar', args=[self.v.pk]))
        self.v.refresh_from_db()
        self.assertEqual(self.v.estado, Vehiculo.AUTORIZADO)


class CrearEditarVehiculoTests(BaseVehiculosTests):
    def test_crear_genera_el_qr_automaticamente(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('vehiculos:crear'), self.datos())
        self.assertRedirects(respuesta, reverse('vehiculos:lista'))
        vehiculo = Vehiculo.objects.get(placa='GSA-3841')
        self.assertTrue(CodigoQR.objects.filter(vehiculo=vehiculo).exists())

    def test_crear_con_errores_vuelve_al_formulario(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('vehiculos:crear'), self.datos(placa='###'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'solo puede contener letras')
        self.assertFalse(Vehiculo.objects.exists())

    def test_formulario_tiene_vista_previa_de_la_placa(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:crear'))
        self.assertContains(respuesta, 'id="placaVista"')
        self.assertContains(respuesta, 'Vista previa de la placa')
        self.assertContains(respuesta, 'Guardar y generar QR')
        self.assertTrue(respuesta.context['hay_propietarios'])

    def test_edicion_muestra_su_placa_en_la_vista_previa(self):
        v = self.vehiculo('GQE-4096')
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:editar', args=[v.pk]))
        self.assertContains(respuesta, 'GQE-4096')
        self.assertNotContains(respuesta, 'Guardar y generar QR')

    def test_sin_propietarios_activos_se_explica(self):
        Propietario.objects.filter(estado=True).update(estado=False)
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:crear'))
        self.assertFalse(respuesta.context['hay_propietarios'])
        self.assertContains(respuesta, 'No hay propietarios activos')


class EliminarVehiculoTests(BaseVehiculosTests):
    def setUp(self):
        self.v = self.vehiculo('GSA-3841')
        HistorialIngreso.objects.create(vehiculo=self.v)
        HistorialIngreso.objects.create(vehiculo=self.v)
        RegistroMovimiento.objects.create(
            codigo_qr=self.v.codigo_qr, vehiculo=self.v, estado=RegistroMovimiento.DENEGADO, detalle='Código expirado')

    def test_resumen_de_lo_que_se_borra(self):
        self.assertEqual(resumen_eliminacion(self.v),
                         {'total_qr': 1, 'total_ingresos': 2, 'total_movimientos': 1})

    def test_la_confirmacion_muestra_las_cifras_reales(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('vehiculos:eliminar', args=[self.v.pk]))
        self.assertEqual(respuesta.context['resumen']['total_ingresos'], 2)
        self.assertContains(respuesta, 'GSA-3841')
        self.assertContains(respuesta, 'irreversible')
        self.assertContains(respuesta, 'Ana Mora Vera')

    def test_sin_marcar_la_casilla_no_se_elimina(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('vehiculos:eliminar', args=[self.v.pk]))
        self.assertRedirects(respuesta, reverse('vehiculos:eliminar', args=[self.v.pk]))
        self.assertTrue(Vehiculo.objects.filter(pk=self.v.pk).exists())

    def test_con_confirmacion_se_elimina_en_cascada_y_no_borra_al_propietario(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('vehiculos:eliminar', args=[self.v.pk]), {'confirmo': 'on'})
        self.assertRedirects(respuesta, reverse('vehiculos:lista'))
        self.assertFalse(Vehiculo.objects.exists())
        self.assertEqual(CodigoQR.objects.count(), 0)
        self.assertEqual(HistorialIngreso.objects.count(), 0)
        self.assertEqual(RegistroMovimiento.objects.count(), 0)
        self.assertTrue(Propietario.objects.filter(pk=self.activo.pk).exists())
