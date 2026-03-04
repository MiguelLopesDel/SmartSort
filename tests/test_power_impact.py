import unittest
from unittest.mock import MagicMock, mock_open, patch

from smartsort.utils.power import PowerManager


class TestPowerImpact(unittest.TestCase):
    def setUp(self):
        self.config = {
            "power_saving": {
                "enabled": True,
                "pause_ai_on_battery": True,
                "throttle_interval_sec": 10,
                "stop_below_percent": 20,
            }
        }
        self.power_manager = PowerManager(self.config)

    @patch("psutil.Process.cpu_percent")
    @patch("psutil.Process.memory_info")
    def test_get_process_resource_usage(self, mock_mem, mock_cpu):
        """Testa a coleta de recursos do processo."""
        mock_cpu.return_value = 5.0
        mock_mem.return_value = MagicMock(rss=100 * 1024 * 1024)

        cpu, mem = self.power_manager.get_process_resource_usage()
        self.assertEqual(cpu, 5.0)
        self.assertEqual(mem, 100.0)

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open, read_data="Battery")
    def test_get_system_discharge_rate_power_now(self, m_open, m_listdir, m_exists):
        """Testa leitura da taxa de descarga via power_now."""
        m_exists.side_effect = lambda p: "power_now" in p or "type" in p or "/sys/class/power_supply/" in p
        m_listdir.return_value = ["BAT0"]

        m_open.side_effect = [mock_open(read_data="Battery").return_value, mock_open(read_data="15000000").return_value]

        rate = self.power_manager.get_system_discharge_rate()
        self.assertEqual(rate, 15.0)

    @patch("psutil.cpu_percent")
    @patch("smartsort.utils.power.PowerManager.get_process_resource_usage")
    @patch("smartsort.utils.power.PowerManager.is_on_battery")
    def test_estimate_app_impact(self, mock_on_batt, mock_res, mock_sys_cpu):
        """Testa a estimativa de impacto do app no sistema."""
        mock_on_batt.return_value = True
        mock_res.return_value = (10.0, 50.0)
        mock_sys_cpu.return_value = 20.0

        impact = self.power_manager.estimate_app_impact()
        self.assertEqual(impact, 50.0)


if __name__ == "__main__":
    unittest.main()
