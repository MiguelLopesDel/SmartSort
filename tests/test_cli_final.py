import unittest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from smartsort.cli.config import app

runner = CliRunner()

class TestCLIFinal(unittest.TestCase):
    @patch("smartsort.cli.config.load_config")
    def test_cli_show(self, mock_load):
        mock_load.return_value = {
            "ai_classification": {"mode": "zero_shot"},
            "acceleration": {"enabled": True, "provider": "auto"},
            "directories_to_watch": ["/tmp"]
        }
        result = runner.invoke(app, ["show"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Configuração SmartSort", result.stdout)

    @patch("smartsort.cli.config.load_config")
    @patch("smartsort.cli.config.save_config", return_value=True)
    def test_cli_model(self, mock_save, mock_load):
        mock_load.return_value = {"ai_classification": {}}
        result = runner.invoke(app, ["model", "test-model"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Modelo alterado para", result.stdout)

    @patch("smartsort.cli.config.load_config")
    def test_cli_status(self, mock_load):
        mock_load.return_value = {
            "ai_classification": {"enabled": False},
            "acceleration": {"enabled": False}
        }
        result = runner.invoke(app, ["status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Status do Sistema", result.stdout)

    @patch("smartsort.cli.config.load_config")
    @patch("smartsort.utils.recommender.HardwareRecommender.show_analysis")
    def test_cli_accel(self, mock_show, mock_load):
        mock_load.return_value = {"acceleration": {}}
        result = runner.invoke(app, ["accel"])
        self.assertEqual(result.exit_code, 0)
        mock_show.assert_called()

    @patch("smartsort.cli.config.load_config")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.abspath", side_effect=lambda x: x)
    @patch("smartsort.cli.config.save_config", return_value=True)
    def test_cli_add(self, mock_save, mock_abs, mock_exists, mock_load):
        mock_load.return_value = {"directories_to_watch": []}
        result = runner.invoke(app, ["add", "/tmp/nova_pasta"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("adicionado", result.stdout)

if __name__ == "__main__":
    unittest.main()
