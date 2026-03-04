import os
import tempfile
import unittest
from unittest.mock import patch

from smartsort.cli.config import add_directory, load_config, save_config, set_model


class TestCLIConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.yaml")
        self.mock_config = {
            "directories_to_watch": ["/tmp/watch"],
            "ai_classification": {"mode": "zero_shot", "zero_shot_model": "old/model"},
            "power_saving": {"enabled": False},
        }

        self.patcher = patch("smartsort.cli.config.os.path.join", return_value=self.config_path)
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_config(self) -> None:
        self.assertTrue(save_config(self.mock_config))
        self.assertTrue(os.path.exists(self.config_path))

        loaded = load_config()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["directories_to_watch"], ["/tmp/watch"])

    def test_add_directory(self) -> None:
        save_config(self.mock_config)
        with patch("smartsort.cli.config.os.path.abspath", return_value="/new/dir"):
            with patch("smartsort.cli.config.os.path.exists", return_value=True):
                add_directory("/new/dir")
                loaded = load_config()
                self.assertIn("/new/dir", loaded["directories_to_watch"])

    def test_set_model(self) -> None:
        save_config(self.mock_config)
        set_model("new/model-v2")
        loaded = load_config()
        self.assertEqual(loaded["ai_classification"]["zero_shot_model"], "new/model-v2")


if __name__ == "__main__":
    unittest.main()
