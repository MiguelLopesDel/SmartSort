import unittest
from unittest.mock import patch, MagicMock
import os
from smartsort.__main__ import load_config, SmartSortHandler, DEFAULT_CONFIG

class TestMain(unittest.TestCase):
    
    @patch("yaml.safe_load")
    @patch("builtins.open")
    @patch("os.path.exists")
    def test_load_config_main(self, mock_exists, mock_file, mock_yaml):
        mock_exists.return_value = True
        mock_yaml.return_value = {"test": True}
        config = load_config("fake_path")
        self.assertEqual(config, {"test": True})

    @patch("smartsort.core.engine.FileProcessor")
    def test_handler_on_created(self, mock_processor):
        handler = SmartSortHandler(mock_processor)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "test.txt"
        
        handler.on_created(event)
        mock_processor.process_file.assert_called_with("test.txt")

if __name__ == "__main__":
    unittest.main()
