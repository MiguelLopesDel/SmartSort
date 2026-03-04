import os
import shutil
import tempfile
import unittest

from smartsort.core.engine import FileProcessor


class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()
        self.config = {
            "directories_to_watch": [self.test_dir],
            "destination_base_folder": self.dest_dir,
            "ai_classification": {"enabled": False},
            "power_saving": {"enabled": False},
            "fallback_rules": {"txt": "Textos"},
        }
        self.processor = FileProcessor(self.config)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.dest_dir)

    def test_file_movement_logic(self):

        test_file = os.path.join(self.test_dir, "documento.txt")
        with open(test_file, "w") as f:
            f.write("conteudo de teste")

        self.processor.process_file(test_file)

        expected_path = os.path.join(self.dest_dir, "Textos", "documento.txt")
        self.assertTrue(os.path.exists(expected_path))
        self.assertFalse(os.path.exists(test_file))

    def test_path_safety_project_root_protection(self):

        root_file = os.path.join(self.processor.project_root, "README.md")
        self.processor.process_file(root_file)
        self.assertTrue(os.path.exists(root_file))


if __name__ == "__main__":
    unittest.main()
