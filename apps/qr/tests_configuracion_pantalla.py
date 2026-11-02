"""Pruebas de la Fase 8: lo que muestra la pantalla de Configuración QR."""
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.qr.models import CodigoQR, ConfiguracionQR

from .tests_configuracion import BaseConfiguracionTests


class PantallaConfiguracionTests(BaseConfiguracionTests):
    def setUp(self):
        self.client.force_login(self.admin)

    def test_muestra_los_tres_parametros_y_el_valor_actual(self):
        configuracion = ConfiguracionQR.get_solo()
        configuracion.expiration_days = 45
        configuracion.renovacion_automatica = True
        configuracion.save()
        respuesta = self.client.get(reverse('qr:configuracion_qr'))
        for texto in ('Solo administrador', 'Vigencia del QR', 'Validación en la garita', 'Renovación automática',
                      'Guardar configuración', 'Última actualización', 'value="45"'):
            self.assertContains(respuesta, texto)
        self.assertContains(respuesta, 'name="activar_qr" class="peer sr-only" id="id_activar_qr" checked')
        self.assertContains(respuesta, 'name="renovacion_automatica" class="peer sr-only" id="id_renovacion_automatica" checked')

    def test_muestra_el_estado_actual_de_los_qr(self):
        for placa, dias, activo in (('GAA-0001', 20, True), ('GAA-0002', 20, True), ('GAA-0003', 2, True),
                                    ('GAA-0004', -3, True), ('GAA-0005', 20, False)):
            vehiculo = self.vehiculo(placa)
            CodigoQR.objects.filter(vehiculo=vehiculo).update(
                fecha_expiracion=timezone.now() + timedelta(days=dias), activo=activo)
        respuesta = self.client.get(reverse('qr:configuracion_qr'))
        self.assertEqual(respuesta.context['contadores'],
                         {'vigentes': 3, 'por_vencer': 1, 'no_vigentes': 2, 'total': 5})
        for texto in ('Estado actual de los QR', 'QR activos', 'Por expirar (≤ 3 días)', 'Expirados o inactivos'):
            self.assertContains(respuesta, texto)
        for filtro in ('vigentes', 'por_vencer', 'no_vigentes'):
            self.assertContains(respuesta, f'{reverse("qr:lista")}?estado={filtro}')

    def test_usa_la_misma_definicion_de_estados_que_la_lista(self):
        self.vehiculo('GAA-0001')
        configuracion = self.client.get(reverse('qr:configuracion_qr')).context['contadores']
        lista = self.client.get(reverse('qr:lista')).context['contadores']
        self.assertEqual(configuracion, lista)

    def test_no_muestra_el_panel_estado_del_motor_ni_datos_inventados(self):
        respuesta = self.client.get(reverse('qr:configuracion_qr'))
        for texto in ('Estado del Motor', 'Latencia', 'Ed25519', 'SHA-256', 'Sincronización', 'biométric',
                      'Antipassback', 'Protocolo de Auditoría', 'Directiva institucional'):
            self.assertNotContains(respuesta, texto)

    def test_avisa_el_impacto_de_apagar_la_validacion_y_pide_confirmacion(self):
        respuesta = self.client.get(reverse('qr:configuracion_qr'))
        self.assertContains(respuesta, 'ningún vehículo podrá ingresar')
        self.assertContains(respuesta, 'window.confirm')
        self.assertContains(respuesta, 'Los QR existentes conservan su fecha de expiración')
        self.assertContains(respuesta, 'la credencial impresa anterior deja de funcionar')

    def test_errores_de_vigencia_se_muestran_junto_al_campo(self):
        respuesta = self.client.post(reverse('qr:configuracion_qr'), {'expiration_days': 400, 'activar_qr': 'on'})
        self.assertContains(respuesta, 'La vigencia debe estar entre 1 y 365 días.')

    def test_el_mensaje_de_confirmacion_se_ve_tras_guardar(self):
        respuesta = self.client.post(
            reverse('qr:configuracion_qr'), {'expiration_days': 75, 'activar_qr': 'on'}, follow=True)
        self.assertContains(respuesta, 'Configuración guardada: vigencia de 75 días')
        self.assertContains(respuesta, 'value="75"')

    def test_no_depende_de_bootstrap(self):
        respuesta = self.client.get(reverse('qr:configuracion_qr'))
        self.assertNotContains(respuesta, 'bootstrap')

    def test_los_limites_del_campo_son_1_y_365(self):
        respuesta = self.client.get(reverse('qr:configuracion_qr'))
        self.assertContains(respuesta, 'min="1"')
        self.assertContains(respuesta, 'max="365"')
        self.assertContains(respuesta, 'Entre 1 y 365 días.')
