import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from smartsort.core.engine import FileProcessor
from smartsort.utils.recommender import HardwareRecommender


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
                "ac_mode": {"enabled": True, "model": "tiny", "use_gpu": False},
                "battery_mode": {"enabled": False},
            },
            "power_saving": {"enabled": False},
            "fallback_rules": {"mp4": "Videos", "mkv": "Videos"},
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.dest_dir, ignore_errors=True)

    @patch("whisper.load_model")
    def test_video_with_audio_classification(self, mock_whisper_load):
        """Testa classificação de vídeo via áudio"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "este é um vídeo sobre finanças"}
        mock_whisper_load.return_value = mock_model

        processor = FileProcessor(self.config)

        video_file = os.path.join(self.test_dir, "test.mp4")
        with open(video_file, "w") as f:
            f.write("dummy")

        with patch.object(processor, "zero_shot_classifier") as mock_clf:
            mock_clf.return_value = {"labels": ["Financas"], "scores": [0.95]}
            processor.process_file(video_file)

        expected = os.path.join(self.dest_dir, "Financas", "test.mp4")
        self.assertTrue(os.path.exists(expected), f"Deve estar em {expected}")

    @patch("whisper.load_model")
    def test_video_fallback_when_whisper_fails(self, mock_whisper_load):
        """Testa fallback para extensão quando Whisper falha"""
        mock_whisper_load.side_effect = Exception("Whisper error")

        processor = FileProcessor(self.config)
        processor.whisper_model = None

        video_file = os.path.join(self.test_dir, "test.mp4")
        with open(video_file, "w") as f:
            f.write("dummy")

        processor.process_file(video_file)

        expected = os.path.join(self.dest_dir, "Videos", "test.mp4")
        self.assertTrue(os.path.exists(expected))

    def test_audio_config_recommendation_logic(self):
        """Testa a lógica de recomendação do HardwareRecommender para áudio"""
        recommender = HardwareRecommender(self.config)
        rec_batt = recommender.recommend_audio_config(on_battery=True)
        self.assertEqual(rec_batt["model"], "tiny")
        self.assertFalse(rec_batt["use_gpu"])

        rec_ac = recommender.recommend_audio_config(on_battery=False)
        self.assertIn(rec_ac["model"], ["tiny", "base"])


if __name__ == "__main__":
    unittest.main()
