import os
import shutil
import tempfile
import unittest

from smartsort.core.engine import FileProcessor


class TestVideoSupport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()
        self.config = {
            "directories_to_watch": [self.test_dir],
            "destination_base_folder": self.dest_dir,
            "ai_classification": {"enabled": True, "mode": "zero_shot"},
            "power_saving": {"enabled": False},
            "fallback_rules": {"mp4": "Videos", "mkv": "Videos", "avi": "Videos"},
        }
        self.processor = FileProcessor(self.config)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.dest_dir)

    def test_video_file_organization_by_fallback(self):
        video_file = os.path.join(self.test_dir, "aula_python.mp4")
        with open(video_file, "wb") as f:
            f.write(b"video binary data")

        self.processor.process_file(video_file)

        expected_path = os.path.join(self.dest_dir, "Videos", "aula_python.mp4")
        self.assertTrue(os.path.exists(expected_path), f"Video deveria estar em {expected_path}")
        self.assertFalse(os.path.exists(video_file))


if __name__ == "__main__":
    unittest.main()
