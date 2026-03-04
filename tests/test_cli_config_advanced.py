import unittest
from unittest.mock import patch

from smartsort.cli.config import set_model, show_config


class TestCliConfigAdvanced(unittest.TestCase):

    @patch("smartsort.cli.config.load_config")
    @patch("smartsort.cli.config.save_config")
    @patch("smartsort.cli.config.console")
    def test_set_model(self, mock_console, mock_save, mock_load):
        mock_load.return_value = {"ai_classification": {}}
        mock_save.return_value = True

        set_model("new_model")

        mock_save.assert_called()
        self.assertEqual(mock_load.return_value["ai_classification"]["zero_shot_model"], "new_model")

    @patch("smartsort.cli.config.load_config")
    @patch("smartsort.cli.config.console")
    def test_show_config(self, mock_console, mock_load):
        mock_load.return_value = {
            "ai_classification": {"mode": "zero_shot"},
            "acceleration": {"enabled": True, "provider": "openvino"},
            "directories_to_watch": ["/tmp"],
        }

        show_config()
        mock_console.print.assert_called()


if __name__ == "__main__":
    unittest.main()
