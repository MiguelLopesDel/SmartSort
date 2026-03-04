import unittest
from unittest.mock import patch

from smartsort.cli.tui import SmartSortTUI


class TestUserInterface(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ai_classification": {"mode": "zero_shot", "enabled": True},
            "acceleration": {"enabled": True, "provider": "auto", "device": "auto"},
            "directories_to_watch": ["/tmp"],
        }

    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.PowerManager")
    def test_tui_initialization_and_status(self, mock_pm, mock_load):
        mock_load.return_value = self.config
        tui = SmartSortTUI()

        with patch(
            "smartsort.utils.recommender.HardwareRecommender.get_best_acceleration", return_value=("cuda", "GPU")
        ):
            tui.pm.is_on_battery.return_value = False
            table = tui.draw_status_summary()
            self.assertIsNotNone(table)

    @patch("smartsort.cli.tui.load_config", return_value=None)
    @patch("smartsort.cli.tui.sys.exit")
    def test_tui_abort_on_config_error(self, mock_exit, mock_load):
        with patch("smartsort.cli.tui.PowerManager"):
            from smartsort.cli.tui import SmartSortTUI

            SmartSortTUI()
            mock_exit.assert_called_with(1)


if __name__ == "__main__":
    unittest.main()
