import unittest
from unittest.mock import patch, mock_open, MagicMock
from smartsort.cli.config import load_config, save_config, add_directory

class TestCliConfig(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data="key: value")
    @patch("yaml.safe_load")
    def test_load_config_success(self, mock_yaml, mock_file):
        mock_yaml.return_value = {"key": "value"}
        config = load_config()
        self.assertEqual(config, {"key": "value"})

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("smartsort.cli.config.logger")
    def test_load_config_not_found(self, mock_logger, mock_file):
        config = load_config()
        self.assertIsNone(config)
        mock_logger.error.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_dump")
    def test_save_config_success(self, mock_yaml, mock_file):
        res = save_config({"key": "value"})
        self.assertTrue(res)
        mock_yaml.assert_called()

    @patch("smartsort.cli.config.load_config")
    @patch("os.path.exists")
    @patch("smartsort.cli.config.save_config")
    def test_add_directory_success(self, mock_save, mock_exists, mock_load):
        mock_load.return_value = {"directories_to_watch": []}
        mock_exists.return_value = True
        
        add_directory("/tmp/test")
        mock_save.assert_called()

if __name__ == "__main__":
    unittest.main()
