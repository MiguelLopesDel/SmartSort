import unittest
from unittest.mock import patch, MagicMock
from smartsort.core.engine import FileProcessor

class TestEngineAdvanced(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ai_classification": {"mode": "zero_shot", "enabled": False},
            "acceleration": {"enabled": False},
            "fallback_rules": {"pdf": "Docs"}
        }

    def test_update_config_no_reload(self):
        processor = FileProcessor(self.config)
        with patch.object(processor, "_load_models") as mock_load:
            new_config = self.config.copy()
            new_config["directories_to_watch"] = ["/new"]
            processor.update_config(new_config)
            mock_load.assert_not_called()

    def test_update_config_with_reload(self):
        processor = FileProcessor(self.config)
        with patch.object(processor, "_load_models") as mock_load:
            new_config = self.config.copy()
            # Garante que os modos são diferentes
            new_config["ai_classification"] = {"mode": "local_ml", "enabled": True}
            processor.update_config(new_config)
            mock_load.assert_called()

    @patch("smartsort.core.engine.logger")
    def test_classify_file_ai_error_fallback(self, mock_logger):
        config = self.config.copy()
        config["ai_classification"]["enabled"] = True
        config["ai_classification"]["mode"] = "zero_shot"
        
        processor = FileProcessor(config)
        processor.zero_shot_classifier = MagicMock(side_effect=Exception("AI Crash"))
        
        cat, conf = processor.classify_file("test.pdf", "test.pdf")
        self.assertEqual(cat, "Docs")
        mock_logger.exception.assert_called()

if __name__ == "__main__":
    unittest.main()
