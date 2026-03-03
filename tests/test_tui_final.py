import unittest
from unittest.mock import patch, MagicMock
from smartsort.cli.tui import SmartSortTUI

class TestTUIFinal(unittest.TestCase):
    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.console.clear")
    @patch("smartsort.cli.tui.IntPrompt.ask")
    def test_tui_main_menu_exit(self, mock_ask, mock_clear, mock_load):
        mock_load.return_value = {
            "ai_classification": {"enabled": False},
            "acceleration": {"enabled": False}
        }

        mock_ask.return_value = 0
        
        tui = SmartSortTUI()
        tui.main_menu()
        
        self.assertEqual(mock_ask.call_count, 1)
        mock_clear.assert_called()

    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.IntPrompt.ask")
    @patch("smartsort.cli.tui.save_config")
    def test_tui_toggle_accel(self, mock_save, mock_ask, mock_load):
        mock_load.return_value = {
            "ai_classification": {"enabled": False},
            "acceleration": {"enabled": False}
        }

        mock_ask.side_effect = [4, 0]

        tui = SmartSortTUI()
        tui.main_menu()

        mock_save.assert_called()
        self.assertTrue(tui.config["acceleration"]["enabled"])

    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.IntPrompt.ask")
    @patch("smartsort.cli.tui.Prompt.ask")
    @patch("smartsort.cli.tui.add_directory")
    def test_tui_add_directory_flow(self, mock_add, mock_prompt, mock_int, mock_load):
        mock_load.return_value = {"ai_classification": {}, "acceleration": {}}

        mock_int.side_effect = [2, 0]
        mock_prompt.return_value = "/home/user/downloads"

        tui = SmartSortTUI()
        tui.main_menu()

        mock_add.assert_called_with("/home/user/downloads")

    @patch("smartsort.cli.tui.load_config")
    @patch("smartsort.cli.tui.IntPrompt.ask")
    @patch("smartsort.cli.tui.Prompt.ask")
    @patch("smartsort.cli.tui.set_model")
    def test_tui_change_model_flow(self, mock_set, mock_prompt, mock_int, mock_load):
        mock_load.return_value = {"ai_classification": {}, "acceleration": {}}

        mock_int.side_effect = [3, 0]
        mock_prompt.return_value = "new-ia-model"

        tui = SmartSortTUI()
        tui.main_menu()

        mock_set.assert_called_with("new-ia-model")

if __name__ == "__main__":
    unittest.main()
