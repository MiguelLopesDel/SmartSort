import unittest
import os
import shutil
from smartsort.cli.config import load_config
from smartsort.core.engine import FileProcessor

class TestPathSafety(unittest.TestCase):
    def test_load_config_from_any_dir(self):
        """Garante que o config é carregado mesmo de um subdiretório qualquer."""

        root_config_path = os.path.join(os.getcwd(), "config", "config.yaml")
        self.assertTrue(os.path.exists(root_config_path), "Root config.yaml deve existir para este teste")


        test_dir = os.path.join(os.getcwd(), "tests", "tmp_dir")
        os.makedirs(test_dir, exist_ok=True)
        
        orig_cwd = os.getcwd()
        try:
            os.chdir(test_dir)

            config = load_config()
            self.assertIsNotNone(config, "Falha ao carregar config de subdiretório")
            self.assertIn("ai_classification", config)
        finally:
            os.chdir(orig_cwd)
            shutil.rmtree(test_dir)

    def test_file_processor_absolute_paths(self):
        """Verifica se o FileProcessor resolve corretamente o root do projeto."""
        config = {
            "destination_base_folder": "data/sorted",
            "ai_classification": {"enabled": False},
            "power_saving": {"enabled": False}
        }
        processor = FileProcessor(config)
        

        self.assertTrue(processor.project_root.endswith("SmartSort"))

        self.assertTrue(os.path.isabs(processor.destination_base))
        self.assertIn(processor.project_root, processor.destination_base)

if __name__ == "__main__":
    unittest.main()
