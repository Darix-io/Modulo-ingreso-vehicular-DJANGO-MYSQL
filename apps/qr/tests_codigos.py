"""Pruebas de la Fase 5: lista de códigos QR, detalle con resumen de accesos y credencial imprimible."""
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.roles import ADMINISTRADOR, PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.models import CodigoQR, HistorialIngreso
from apps.qr.services.codigos import (
    buscar_codigos, contadores_qr, filtrar_por_estado, resumen_accesos, vigencia_qr)
from apps.qr.services.estadisticas import resumen_dashboard
from apps.usuarios.models import Rol
from apps.vehiculos.models import Vehiculo


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class BaseCodigosQRTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        cls.admin = Usuario.objects.create_user(
            username='adm', email='adm@example.com', cedula='0900000001', password='Clave12345!',
            first_name='Carlos', last_name='Mendoza', rol=Rol.objects.create(nombre=ADMINISTRADOR))
        cls.guardia = Usuario.objects.create_user(
            username='gua', email='gua@example.com', cedula='0900000002', password='Clave12345!',
            first_name='Víctor', last_name='Morán', rol=Rol.objects.create(nombre=PERSONAL_SEGURIDAD))
        cls.propietario = Propietario.objects.create(
            nombre='Ana Mora Vera', numero_identidad='0912345678', celular='0991234567',
            correo='ana@unemi.edu.ec', tipo='Docente')

    def qr(self, placa, dias=20, activo=True):
        """Crea un vehículo y deja su QR venciendo dentro de `dias` días (negativo = ya venció)."""
        vehiculo = Vehiculo.objects.create(
            propietario=self.propietario, placa=placa, marca='Kia', modelo='Rio', color='Gris')
        vence = timezone.now() + timedelta(days=dias)
        CodigoQR.objects.filter(vehiculo=vehiculo).update(
            fecha_expiracion=vence, fecha_creacion=vence - timedelta(days=30), activo=activo)
        return CodigoQR.objects.get(vehiculo=vehiculo)


class VigenciaQRTests(BaseCodigosQRTests):
    def test_estados_de_vigencia(self):
        vigente = vigencia_qr(self.qr('GAA-0001', dias=20))
        por_vencer = vigencia_qr(self.qr('GAA-0002', dias=2))
        expirado = vigencia_qr(self.qr('GAA-0003', dias=-4))
        inactivo = vigencia_qr(self.qr('GAA-0004', dias=20, activo=False))
        self.assertEqual((vigente['clave'], vigente['tono']), ('vigente', 'verde'))
        self.assertEqual((por_vencer['clave'], por_vencer['tono']), ('por_vencer', 'ambar'))
        self.assertEqual((expirado['clave'], expirado['tono']), ('expirado', 'rojo'))
        self.assertEqual((inactivo['clave'], inactivo['tono']), ('inactivo', 'gris'))
        self.assertEqual(expirado['dias_vencido'], 4)
        self.assertEqual(expirado['porcentaje'], 100)
        self.assertTrue(por_vencer['es_vigente'])
        self.assertFalse(expirado['es_vigente'])
        self.assertFalse(inactivo['es_vigente'])

    def test_dias_restantes_y_porcentaje(self):
        datos = vigencia_qr(self.qr('GAA-0005', dias=20))      # vida de 30 días, quedan 20
        self.assertEqual(datos['dias_restantes'], 20)
        self.assertIn(datos['porcentaje'], (33, 34))

    def test_limite_de_tres_dias_cuenta_como_por_vencer(self):
        self.assertEqual(vigencia_qr(self.qr('GAA-0006', dias=3))['clave'], 'por_vencer')
        self.assertEqual(vigencia_qr(self.qr('GAA-0007', dias=4))['clave'], 'vigente')

    def test_contadores_y_filtros(self):
        self.qr('GAA-0001', dias=20)
        self.qr('GAA-0002', dias=2)
        self.qr('GAA-0003', dias=-4)
        self.qr('GAA-0004', dias=20, activo=False)
        ahora = timezone.now()
        base = CodigoQR.objects.all()
        self.assertEqual(contadores_qr(base, ahora),
                         {'vigentes': 2, 'por_vencer': 1, 'no_vigentes': 2, 'total': 4})
        self.assertEqual(filtrar_por_estado(base, 'por_vencer', ahora).count(), 1)
        self.assertEqual(filtrar_por_estado(base, 'no_vigentes', ahora).count(), 2)
        self.assertEqual(filtrar_por_estado(base, '', ahora).count(), 4)
        self.assertEqual(buscar_codigos(base, 'gaa-0003').count(), 1)
        self.assertEqual(buscar_codigos(base, 'Ana Mora').count(), 4)
        self.assertEqual(buscar_codigos(base, '0912345678').count(), 4)

    def test_el_panel_usa_la_misma_definicion_de_qr_activos(self):
        self.qr('GAA-0001', dias=20)
        self.qr('GAA-0002', dias=2)
        self.qr('GAA-0003', dias=-4)
        cuentas = contadores_qr(CodigoQR.objects.all(), timezone.now())
        panel = resumen_dashboard()
        self.assertEqual(panel['qr_activos'], cuentas['vigentes'])
        self.assertEqual(panel['qr_proximos_vencer'], cuentas['por_vencer'])


class ResumenAccesosTests(BaseCodigosQRTests):
    def ingreso(self, vehiculo, momento, guardia=None):
        registro = HistorialIngreso.objects.create(vehiculo=vehiculo, usuario_validador=guardia)
        HistorialIngreso.objects.filter(pk=registro.pk).update(fecha_ingreso=momento)

    def test_sin_ingresos(self):
        resumen = resumen_accesos(self.qr('GAA-0001').vehiculo)
        self.assertIsNone(resumen['ultimo_ingreso'])
        self.assertIsNone(resumen['guardia'])
        self.assertEqual(resumen['total_mes'], 0)

    def test_ultimo_ingreso_guardia_y_total_del_mes(self):
        vehiculo = self.qr('GAA-0001').vehiculo
        otro = self.qr('GAA-0002').vehiculo
        ahora = timezone.now()
        inicio_mes = timezone.localtime(ahora).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        self.ingreso(vehiculo, inicio_mes - timedelta(days=2), self.admin)   # mes pasado: no cuenta
        self.ingreso(vehiculo, inicio_mes + timedelta(minutes=5), self.admin)
        self.ingreso(vehiculo, ahora - timedelta(minutes=1), self.guardia)   # el más reciente
        self.ingreso(otro, ahora - timedelta(minutes=2), self.admin)         # de otro vehículo

        resumen = resumen_accesos(vehiculo, ahora)
        self.assertEqual(resumen['guardia'], 'Víctor Morán')
        self.assertEqual(resumen['total_mes'], 2)
        self.assertEqual(resumen['total_historico'], 3)
        self.assertEqual(resumen['ultimo_ingreso'].usuario_validador, self.guardia)


class ListaCodigosQRTests(BaseCodigosQRTests):
    def setUp(self):
        self.qr('GAA-0001', dias=20)
        self.qr('GAA-0002', dias=2)
        self.qr('GAA-0003', dias=-4)
        self.qr('GBB-0004', dias=20, activo=False)

    def test_contadores_en_pantalla(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:lista'))
        self.assertEqual(respuesta.context['contadores'],
                         {'vigentes': 2, 'por_vencer': 1, 'no_vigentes': 2, 'total': 4})
        self.assertContains(respuesta, 'QR activos')
        self.assertContains(respuesta, 'Próximos a vencer')
        self.assertContains(respuesta, 'Expirados o inactivos')

    def test_no_hay_boton_para_generar_codigos_ni_datos_inventados(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:lista'))
        for prohibido in ('Generar código', 'Generar Código', 'Renovaciones del mes',
                          'firma criptográfica', 'Exportar listado'):
            self.assertNotContains(respuesta, prohibido)

    def test_filtra_por_estado(self):
        self.client.force_login(self.admin)
        for estado, esperado in (('vigentes', 2), ('por_vencer', 1), ('no_vigentes', 2), ('inventado', 4)):
            respuesta = self.client.get(reverse('qr:lista'), {'estado': estado})
            self.assertEqual(len(respuesta.context['qrs']), esperado, estado)

    def test_busqueda_por_placa_y_contadores_respetan_la_busqueda(self):
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:lista'), {'q': 'GBB'})
        self.assertEqual([q.vehiculo.placa for q in respuesta.context['qrs']], ['GBB-0004'])
        self.assertEqual(respuesta.context['contadores']['total'], 1)

    def test_cada_fila_trae_su_vigencia_y_el_estado(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:lista'))
        claves = {q.vehiculo.placa: q.vigencia['clave'] for q in respuesta.context['qrs']}
        self.assertEqual(claves, {'GAA-0001': 'vigente', 'GAA-0002': 'por_vencer',
                                  'GAA-0003': 'expirado', 'GBB-0004': 'inactivo'})
        self.assertContains(respuesta, 'Por vencer')
        self.assertContains(respuesta, 'Expiró hace 4 días')

    def test_un_qr_que_expiro_hace_horas_dice_expiro_hoy(self):
        codigo = CodigoQR.objects.get(vehiculo__placa='GAA-0003')
        CodigoQR.objects.filter(pk=codigo.pk).update(fecha_expiracion=timezone.now() - timedelta(hours=2))
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:lista'), {'estado': 'no_vigentes'})
        self.assertContains(respuesta, 'Expiró hoy')
        self.assertNotContains(respuesta, 'Expiró hace 0')

    def test_paginacion_conserva_el_filtro(self):
        for n in range(10, 30):
            self.qr(f'GZZ-{n:04d}', dias=20)
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:lista'), {'estado': 'vigentes'})
        self.assertContains(respuesta, 'page=2')
        self.assertContains(respuesta, 'estado=vigentes')

    def test_renovar_sigue_siendo_post_y_cambia_el_token(self):
        codigo = CodigoQR.objects.get(vehiculo__placa='GAA-0003')
        token = codigo.contenido
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('qr:renovar', args=[codigo.pk])).status_code, 405)
        self.client.post(reverse('qr:renovar', args=[codigo.pk]))
        codigo.refresh_from_db()
        self.assertNotEqual(codigo.contenido, token)
        self.assertTrue(codigo.activo)
        self.assertFalse(codigo.is_expired)


class RenovarSoloAdministradorTests(BaseCodigosQRTests):
    def test_seguridad_recibe_403_y_el_token_no_cambia(self):
        codigo = self.qr('GAA-0003')
        token = codigo.contenido
        self.client.force_login(self.guardia)
        self.assertEqual(self.client.post(reverse('qr:renovar', args=[codigo.pk])).status_code, 403)
        codigo.refresh_from_db()
        self.assertEqual(codigo.contenido, token)

    def test_boton_renovar_oculto_para_seguridad_en_lista_y_detalle(self):
        codigo = self.qr('GAA-0003')
        url_renovar = reverse('qr:renovar', args=[codigo.pk])
        self.client.force_login(self.guardia)
        for pagina in (reverse('qr:lista'), reverse('qr:detalle', args=[codigo.pk])):
            self.assertNotContains(self.client.get(pagina), url_renovar)

    def test_boton_renovar_visible_para_el_administrador(self):
        codigo = self.qr('GAA-0003')
        url_renovar = reverse('qr:renovar', args=[codigo.pk])
        self.client.force_login(self.admin)
        for pagina in (reverse('qr:lista'), reverse('qr:detalle', args=[codigo.pk])):
            self.assertContains(self.client.get(pagina), url_renovar)

    def test_seguridad_sigue_viendo_descargando_e_imprimiendo(self):
        codigo = self.qr('GAA-0003')
        self.client.force_login(self.guardia)
        for nombre in ('qr:detalle', 'qr:credencial', 'qr:descargar'):
            self.assertEqual(self.client.get(reverse(nombre, args=[codigo.pk])).status_code, 200)


class DetalleCodigoQRTests(BaseCodigosQRTests):
    def test_muestra_vigencia_vehiculo_propietario_y_resumen_de_accesos(self):
        codigo = self.qr('GSA-3841', dias=20)
        HistorialIngreso.objects.create(vehiculo=codigo.vehiculo, usuario_validador=self.guardia)
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:detalle', args=[codigo.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['vigencia']['clave'], 'vigente')
        self.assertEqual(respuesta.context['accesos']['total_mes'], 1)
        for texto in ('GSA-3841', 'Ana Mora Vera', '0912345678', 'ana@unemi.edu.ec', 'Resumen de accesos',
                      'Último ingreso registrado', 'Víctor Morán', 'Total de ingresos este mes', 'Renovar QR'):
            self.assertContains(respuesta, texto)
        self.assertContains(respuesta, reverse('qr:credencial', args=[codigo.pk]))

    def test_sin_ingresos_lo_explica(self):
        codigo = self.qr('GSA-3841')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('qr:detalle', args=[codigo.pk])),
                            'aún no tiene ingresos autorizados')

    def test_no_muestra_el_codigo_secreto_completo(self):
        codigo = self.qr('GSA-3841')
        self.client.force_login(self.guardia)
        self.assertNotContains(self.client.get(reverse('qr:detalle', args=[codigo.pk])), str(codigo.contenido))

    def test_advierte_si_el_codigo_no_es_valido(self):
        codigo = self.qr('GSA-3841', dias=-2)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('qr:detalle', args=[codigo.pk])), 'no permite el ingreso')

    def test_renovar_desde_el_detalle_es_post_y_vuelve_al_detalle(self):
        codigo = self.qr('GSA-3841', dias=-2)
        detalle = reverse('qr:detalle', args=[codigo.pk])
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('qr:renovar', args=[codigo.pk]), {'next': detalle})
        self.assertRedirects(respuesta, detalle)


class CredencialQRTests(BaseCodigosQRTests):
    def test_ruta_y_contenido(self):
        codigo = self.qr('GSA-3841', dias=20)
        self.assertEqual(reverse('qr:credencial', args=[codigo.pk]), f'/qr/credencial/{codigo.pk}/')
        self.client.force_login(self.guardia)
        respuesta = self.client.get(reverse('qr:credencial', args=[codigo.pk]))
        self.assertEqual(respuesta.status_code, 200)
        vence = timezone.localtime(codigo.fecha_expiracion).strftime('%d/%m/%Y')
        for texto in ('GaritaQR', 'GSA-3841', 'Ana Mora Vera', vence, 'Colocar en el parabrisas',
                      'window.print()', codigo.imagen.url):
            self.assertContains(respuesta, texto)
        self.assertNotContains(respuesta, 'no es válida')

    def test_es_una_pagina_limpia_sin_el_menu(self):
        codigo = self.qr('GSA-3841')
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:credencial', args=[codigo.pk]))
        for menu in ('Panel de control', 'Cerrar sesión', 'Sistema activo'):
            self.assertNotContains(respuesta, menu)

    def test_avisa_si_la_credencial_esta_vencida(self):
        codigo = self.qr('GSA-3841', dias=-3)
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('qr:credencial', args=[codigo.pk]))
        self.assertContains(respuesta, 'no es válida')
        self.assertContains(respuesta, 'expiró')

    def test_requiere_iniciar_sesion(self):
        codigo = self.qr('GSA-3841')
        respuesta = self.client.get(reverse('qr:credencial', args=[codigo.pk]))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/login/', respuesta.url)

    def test_codigo_inexistente_da_404(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('qr:credencial', args=[99999])).status_code, 404)
