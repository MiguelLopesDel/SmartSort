import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from smartsort.core.engine import FileProcessor


class TestVideoSupport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()
        self.config = {
            "directories_to_watch": [self.test_dir],
            "destination_base_folder": self.dest_dir,
            "ai_classification": {"enabled": True, "mode": "zero_shot"},
            "audio_classification": {
                "enabled": True,
                "sample_duration_sec": 10,
                "ac_mode": {"enabled": True, "model": "tiny", "use_gpu": False},
                "battery_mode": {"enabled": False},
            },
            "power_saving": {"enabled": False},
            "fallback_rules": {"mp4": "Videos"},
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.dest_dir)

    def test_video_fallback_when_whisper_disabled(self):
        self.config["audio_classification"]["enabled"] = False
        processor = FileProcessor(self.config)

        video_file = os.path.join(self.test_dir, "teste.mp4")
        with open(video_file, "w") as f:
            f.write("dummy")

        processor.process_file(video_file)
        self.assertTrue(os.path.exists(os.path.join(self.dest_dir, "Videos", "teste.mp4")))

    @patch("whisper.load_model")
    def test_video_classification_via_simulated_audio(self, mock_whisper_load):

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "este é um video sobre finanças e faturas"}
        mock_whisper_load.return_value = mock_model

        processor = FileProcessor(self.config)

        video_file = os.path.join(self.test_dir, "fatura_internet.mp4")
        with open(video_file, "w") as f:
            f.write("dummy")

        with patch.object(processor, "zero_shot_classifier") as mock_classifier:
            mock_classifier.return_value = {"labels": ["Financas"], "scores": [0.99]}

            processor.process_file(video_file)

            expected_path = os.path.join(self.dest_dir, "Financas", "fatura_internet.mp4")
            self.assertTrue(os.path.exists(expected_path), f"Deveria estar em {expected_path}")


if __name__ == "__main__":
    unittest.main()
