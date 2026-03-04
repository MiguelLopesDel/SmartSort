import os
import unittest

import yaml

from smartsort.core.engine import FileProcessor


class TestSmoke(unittest.TestCase):
    def test_real_config_validity(self):

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, "config", "config.yaml")

        self.assertTrue(os.path.exists(config_path))
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            self.assertIsNotNone(config)
            self.assertIn("ai_classification", config)

    def test_processor_with_minimal_valid_config(self):

        config = {
            "directories_to_watch": [],
            "destination_base_folder": "/tmp/sorted",
            "ai_classification": {"enabled": False},
            "power_saving": {"enabled": False},
        }
        processor = FileProcessor(config)
        self.assertIsNotNone(processor)


if __name__ == "__main__":
    unittest.main()
