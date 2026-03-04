import unittest
from unittest.mock import MagicMock, patch

from smartsort.utils.recommender import HardwareRecommender


class TestHardwareRecommender(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {"acceleration": {"enabled": True}}
        self.recommender = HardwareRecommender(self.config)

    @patch("platform.processor", return_value="Intel(R) Core(TM)")
    @patch("smartsort.utils.recommender.HardwareRecommender._check_nvidia_gpu", return_value=False)
    def test_intel_cpu_recommendation(self, mock_nvidia, mock_processor) -> None:
        """Testa se recomenda OpenVINO para CPU Intel quando não há bateria."""
        provider, device = self.recommender.get_best_acceleration(on_battery=False)
        self.assertEqual(provider, "openvino")
        self.assertEqual(device, "GPU")

        provider_batt, device_batt = self.recommender.get_best_acceleration(on_battery=True)
        self.assertEqual(provider_batt, "openvino")
        self.assertEqual(device_batt, "GPU")

    @patch("platform.processor", return_value="AMD Ryzen")
    @patch("smartsort.utils.recommender.HardwareRecommender._check_nvidia_gpu", return_value=False)
    def test_amd_cpu_recommendation(self, mock_nvidia, mock_processor) -> None:
        """Testa se recomenda OpenVINO para CPU AMD."""
        provider, device = self.recommender.get_best_acceleration(on_battery=False)
        self.assertEqual(provider, "openvino")

    @patch("platform.processor", return_value="Unknown")
    @patch("smartsort.utils.recommender.HardwareRecommender._check_nvidia_gpu", return_value=True)
    def test_nvidia_gpu_recommendation(self, mock_nvidia, mock_processor) -> None:
        """Testa se prioriza CUDA quando tem placa Nvidia."""
        provider, device = self.recommender.get_best_acceleration(on_battery=False)
        self.assertEqual(provider, "cuda")
        self.assertEqual(device, "GPU")

    @patch("smartsort.utils.recommender.logger")
    @patch("psutil.sensors_battery")
    def test_show_analysis(self, mock_battery, mock_logger) -> None:
        """Testa o print do relatório de análise."""
        mock_battery.return_value = MagicMock(power_plugged=False)
        self.recommender.show_analysis()
        self.assertTrue(mock_logger.info.called)


if __name__ == "__main__":
    unittest.main()
