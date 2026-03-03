import unittest
from unittest.mock import patch, MagicMock
import sys
from smartsort.cli.tui import SmartSortTUI, start_tui

class TestTUIExtreme(unittest.TestCase):
    @patch("smartsort.cli.tui.load_config", return_value=None)
    @patch("smartsort.cli.tui.sys.exit")
    def test_tui_init_fail(self, mock_exit, mock_load):

        SmartSortTUI()
        mock_exit.assert_called_with(1)

    @patch("smartsort.cli.tui.load_config")
    @patch("os.path.exists", return_value=False)
    @patch("smartsort.cli.tui.Prompt.ask")
    def test_tui_show_logs_not_found(self, mock_ask, mock_exists, mock_load):
        mock_load.return_value = {"ai_classification": {}, "acceleration": {}}
        tui = SmartSortTUI()
        tui.show_logs()


    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.IntPrompt.ask")
    @patch("smartsort.cli.tui.show_status")
    @patch("smartsort.cli.tui.Prompt.ask")
    def test_tui_menu_status_flow(self, mock_prompt, mock_status, mock_int, mock_load):
        mock_load.return_value = {"ai_classification": {}, "acceleration": {}}

        mock_int.side_effect = [1, 0]
        
        tui = SmartSortTUI()
        tui.main_menu()
        
        mock_status.assert_called()

    @patch("smartsort.cli.tui.SmartSortTUI")
    def test_start_tui_wrapper(self, mock_tui_class):

        start_tui()
        mock_tui_class.return_value.main_menu.assert_called()

if __name__ == "__main__":
    unittest.main()
