import unittest
from unittest.mock import patch, MagicMock
import os
from smartsort.__main__ import load_config, SmartSortHandler, DEFAULT_CONFIG, main

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

    @patch("smartsort.__main__.load_config")
    @patch("smartsort.__main__.FileProcessor")
    @patch("smartsort.__main__.Observer")
    @patch("time.sleep", side_effect=KeyboardInterrupt)
    @patch("os.path.exists", return_value=True)
    def test_main_loop_keyboard_interrupt(self, mock_exists, mock_sleep, mock_obs, mock_proc, mock_load):

        mock_load.return_value = DEFAULT_CONFIG
        

        try:
            main()
        except KeyboardInterrupt:
            pass
        
        mock_obs.return_value.start.assert_called()
        mock_obs.return_value.stop.assert_called()

if __name__ == "__main__":
    unittest.main()
