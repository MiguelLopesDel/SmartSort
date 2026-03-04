import os
import unittest

import yaml

from smartsort.core.engine import FileProcessor


class TestSmoke(unittest.TestCase):
    def test_config_yaml_is_valid(self):
        """Garante que o config.yaml atual é válido e pode ser lido."""
        config_path = "config/config.yaml"
        self.assertTrue(os.path.exists(config_path), f"{config_path} não existe!")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            self.assertIsNotNone(config)
            self.assertIn("ai_classification", config)
            self.assertIn("directories_to_watch", config)

    def test_processor_initialization_with_real_config(self):
        """Garante que o FileProcessor inicia sem crashar com o config.yaml real."""
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        config["ai_classification"]["enabled"] = False

        try:
            processor = FileProcessor(config)
            self.assertIsNotNone(processor)
        except Exception as e:
            self.fail(f"FileProcessor falhou ao iniciar com config real: {e}")


if __name__ == "__main__":
    unittest.main()
