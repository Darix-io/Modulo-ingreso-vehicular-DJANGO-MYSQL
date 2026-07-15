from django.test import TestCase

from apps.qr.models import ConfiguracionQR


class ConfiguracionQRTests(TestCase):
    def test_get_solo_creates_singleton(self):
        config = ConfiguracionQR.get_solo()
        self.assertIsNotNone(config)
        self.assertEqual(config.id, 1)

        config.expiration_days = 45
        config.save()

        same_config = ConfiguracionQR.get_solo()
        self.assertEqual(same_config.id, config.id)
        self.assertEqual(same_config.expiration_days, 45)

    def test_get_solo_returns_existing(self):
        first = ConfiguracionQR.get_solo()
        second = ConfiguracionQR.get_solo()
        self.assertEqual(first.pk, second.pk)
