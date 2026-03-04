import unittest
from unittest.mock import MagicMock, mock_open, patch

from smartsort.utils.power import PowerManager


class TestPowerManager(unittest.TestCase):
    def setUp(self):
        self.config = {
            "power_saving": {
                "enabled": True,
                "pause_ai_on_battery": True,
                "throttle_interval_sec": 10,
                "stop_below_percent": 20,
            }
        }
        self.pm = PowerManager(self.config)

    @patch("psutil.sensors_battery")
    def test_battery_status_detection(self, mock_battery):
        mock_battery.return_value = MagicMock(power_plugged=False, percent=50)
        self.assertTrue(self.pm.is_on_battery())
        self.assertEqual(self.pm.get_battery_percent(), 50)

    @patch("psutil.sensors_battery")
    def test_processing_stop_on_low_battery(self, mock_battery):
        mock_battery.return_value = MagicMock(power_plugged=False, percent=15)
        self.assertTrue(self.pm.should_stop_processing())

    @patch("psutil.Process.cpu_percent")
    @patch("psutil.Process.memory_info")
    def test_process_resource_usage_collection(self, mock_mem, mock_cpu):
        mock_cpu.return_value = 5.0
        mock_mem.return_value = MagicMock(rss=100 * 1024 * 1024)
        cpu, mem = self.pm.get_process_resource_usage()
        self.assertEqual(cpu, 5.0)
        self.assertEqual(mem, 100.0)

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_system_discharge_rate_reading(self, m_open, m_listdir, m_exists):
        m_exists.side_effect = lambda p: "power_now" in p or "type" in p or "/sys/class/power_supply/" in p
        m_listdir.return_value = ["BAT0"]
        m_open.side_effect = [mock_open(read_data="Battery").return_value, mock_open(read_data="15000000").return_value]
        rate = self.pm.get_system_discharge_rate()
        self.assertEqual(rate, 15.0)

    @patch("psutil.cpu_percent")
    @patch("smartsort.utils.power.PowerManager.get_process_resource_usage")
    @patch("smartsort.utils.power.PowerManager.is_on_battery")
    def test_app_energy_impact_estimation(self, mock_on_batt, mock_res, mock_sys_cpu):
        mock_on_batt.return_value = True
        mock_res.return_value = (10.0, 50.0)
        mock_sys_cpu.return_value = 20.0
        impact = self.pm.estimate_app_impact()
        self.assertEqual(impact, 50.0)


if __name__ == "__main__":
    unittest.main()
