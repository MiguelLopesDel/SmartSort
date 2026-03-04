import unittest
from unittest.mock import MagicMock, patch

from smartsort.core.engine import FileProcessor
from smartsort.utils.power import PowerManager


class TestBatteryOptimization(unittest.TestCase):
    def setUp(self):
        self.config = {
            "power_saving": {
                "enabled": True,
                "pause_ai_on_battery": True,
                "throttle_interval_sec": 10,
                "stop_below_percent": 20,
            },
            "ai_classification": {"enabled": True, "mode": "api"},
            "destination_base_folder": "data/sorted",
            "fallback_rules": {"pdf": "Documentos", "jpg": "Imagens"},
        }
        self.power_manager = PowerManager(self.config)

    @patch("psutil.sensors_battery")
    def test_is_on_battery_true(self, mock_battery):
        """Testa se detecta corretamente quando está na bateria."""
        mock_battery.return_value = MagicMock(power_plugged=False, percent=50)
        self.assertTrue(self.power_manager.is_on_battery())

    @patch("psutil.sensors_battery")
    def test_is_on_battery_false(self, mock_battery):
        """Testa se detecta corretamente quando está na tomada."""
        mock_battery.return_value = MagicMock(power_plugged=True, percent=100)
        self.assertFalse(self.power_manager.is_on_battery())

    @patch("psutil.sensors_battery")
    def test_should_stop_on_low_battery(self, mock_battery):
        """Testa se interrompe o processamento em 15% (limite é 20%)."""
        mock_battery.return_value = MagicMock(power_plugged=False, percent=15)
        self.assertTrue(self.power_manager.should_stop_processing())

    @patch("psutil.sensors_battery")
    def test_should_not_stop_on_safe_battery(self, mock_battery):
        """Testa se continua processando em 50%."""
        mock_battery.return_value = MagicMock(power_plugged=False, percent=50)
        self.assertFalse(self.power_manager.should_stop_processing())

    @patch("psutil.sensors_battery")
    def test_throttle_interval_on_battery(self, mock_battery):
        """Testa se o intervalo aumenta na bateria."""
        mock_battery.return_value = MagicMock(power_plugged=False, percent=50)
        self.assertEqual(self.power_manager.get_throttle_interval(), 10)

    @patch("psutil.sensors_battery")
    def test_ai_skip_on_battery(self, mock_battery):
        """Verifica se o FileProcessor pula a IA quando está na bateria."""
        mock_battery.return_value = MagicMock(power_plugged=False, percent=50)

        processor = FileProcessor(self.config)
        result = processor.classify_file("teste.pdf", "teste.pdf")

        category = result[0] if isinstance(result, (tuple, list)) else result
        self.assertEqual(category, "Documentos")

    @patch("psutil.sensors_battery")
    def test_ai_runs_on_ac_power(self, mock_battery):
        """Verifica se a IA roda normalmente quando está na tomada."""
        mock_battery.return_value = MagicMock(power_plugged=True, percent=100)

        processor = FileProcessor(self.config)

        with patch.object(FileProcessor, "extract_text_from_pdf", return_value="Texto de Teste"):
            with patch.object(FileProcessor, "simulate_ai_classification", return_value="Financas"):
                result = processor.classify_file("teste.pdf", "teste.pdf")
                category = result[0] if isinstance(result, (tuple, list)) else result
                self.assertEqual(category, "Financas")


if __name__ == "__main__":
    unittest.main()
