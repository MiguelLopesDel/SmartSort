import unittest
from unittest.mock import patch, MagicMock
from smartsort.utils.recommender import HardwareRecommender

class TestHardwareRecommender(unittest.TestCase):
    def setUp(self):
        self.config = {}
        self.recommender = HardwareRecommender(self.config)

    @patch("platform.processor")
    @patch("smartsort.utils.recommender.HardwareRecommender._check_nvidia_gpu")
    def test_get_best_acceleration_nvidia(self, mock_gpu, mock_proc):
        mock_gpu.return_value = True
        mock_proc.return_value = "x86_64"
        
        p, d = self.recommender.get_best_acceleration(on_battery=False)
        self.assertEqual(p, "cuda")
        self.assertEqual(d, "GPU")

    @patch("platform.processor")
    @patch("smartsort.utils.recommender.HardwareRecommender._check_nvidia_gpu")
    def test_get_best_acceleration_intel_battery(self, mock_gpu, mock_proc):
        mock_gpu.return_value = False
        mock_proc.return_value = "Intel(R) Core(TM) i7"
        
        p, d = self.recommender.get_best_acceleration(on_battery=True)
        self.assertEqual(p, "openvino")
        self.assertEqual(d, "GPU")

    @patch("psutil.sensors_battery")
    @patch("platform.processor")
    @patch("smartsort.utils.recommender.logger")
    def test_show_analysis(self, mock_logger, mock_proc, mock_batt):
        mock_proc.return_value = "AMD Ryzen"
        mock_batt.return_value = MagicMock(power_plugged=True)
        
        self.recommender.show_analysis()
        mock_logger.info.assert_called()

if __name__ == "__main__":
    unittest.main()
