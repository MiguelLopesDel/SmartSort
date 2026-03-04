import os
import unittest
import unittest.mock
from unittest.mock import patch

from smartsort.cli.tui import SmartSortTUI


class TestTUIAdvanced(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ai_classification": {"mode": "zero_shot", "enabled": True},
            "acceleration": {"enabled": True, "provider": "auto", "device": "auto"},
            "directories_to_watch": ["/tmp"],
        }

    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.PowerManager")
    def test_tui_status_summary(self, mock_pm, mock_load):
        mock_load.return_value = self.config
        tui = SmartSortTUI()

        with patch(
            "smartsort.utils.recommender.HardwareRecommender.get_best_acceleration", return_value=("cuda", "GPU")
        ):
            tui.pm.is_on_battery.return_value = False
            table = tui.draw_status_summary()
            self.assertIsNotNone(table)
            columns = [col.header for col in table.columns]
            self.assertIn("Monitorando", columns)
            self.assertIn("Energia", columns)

    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.PowerManager")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="log line 1\nlog line 2")
    @patch("os.path.exists", return_value=True)
    def test_tui_show_logs(self, mock_exists, mock_file, mock_pm, mock_load):
        mock_load.return_value = self.config
        tui = SmartSortTUI()

        with patch("smartsort.cli.tui.Prompt.ask", return_value=""):
            tui.show_logs(lines=2)

            call_args = mock_file.call_args[0][0]
            self.assertTrue(os.path.isabs(call_args))
            self.assertTrue(call_args.endswith("data/smartsort.log"))


if __name__ == "__main__":
    unittest.main()
