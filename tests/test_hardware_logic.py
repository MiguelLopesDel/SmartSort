import unittest
from unittest.mock import patch

from smartsort.core.engine import FileProcessor


class TestHardwareLogicDecision(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ai_classification": {
                "enabled": True,
                "mode": "zero_shot",
                "zero_shot_model": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
            },
            "acceleration": {"enabled": True, "provider": "openvino", "device": "gpu"},
            "power_saving": {"enabled": True, "pause_ai_on_battery": True},
            "fallback_rules": {"pdf": "Documentos"},
            "destination_base_folder": "data/sorted",
        }

    @patch("smartsort.core.engine.PowerManager")
    @patch("smartsort.core.engine.pipeline")
    def test_should_skip_ai_on_battery(self, mock_pipe, MockPowerManager):
        """Verifica se a IA é pulada quando a bateria está ativa."""
        mock_pm = MockPowerManager.return_value
        mock_pm.should_use_fallback.return_value = True

        processor = FileProcessor(self.config)
        processor.power_manager = mock_pm

        result = processor.classify_file("test.pdf", "test.pdf")
        category = result[0] if isinstance(result, (tuple, list)) else result
        self.assertEqual(category, "Documentos")

    @patch("smartsort.core.engine.pipeline")
    def test_cuda_acceleration_selection(self, mock_pipe):
        """Verifica se o provider 'cuda' passa device=0 para o pipeline."""
        config = self.config.copy()
        config["acceleration"]["provider"] = "cuda"

        FileProcessor(config)

        # O pipeline deve ter sido chamado com device=0
        mock_pipe.assert_called()
        found_cuda = False
        for call in mock_pipe.call_args_list:
            if call.kwargs.get("device") == 0:
                found_cuda = True
        self.assertTrue(found_cuda, "Pipeline não foi chamado com device=0 para CUDA")

    @patch("smartsort.core.engine.pipeline")
    def test_openvino_acceleration_selection(self, mock_pipe):
        """Verifica se o provider 'openvino' tenta carregar a classe correta via import local."""
        config = self.config.copy()
        config["acceleration"]["provider"] = "openvino"
        config["acceleration"]["device"] = "gpu"

        # Mock do import local do optimum
        with patch("builtins.__import__", side_effect=ImportError):
            FileProcessor(config)
            # Como falhou o import (pelo side_effect), deve ter chamado o pipeline padrão
            self.assertTrue(mock_pipe.called)

    @patch("smartsort.core.engine.pipeline")
    def test_cpu_fallback_logic(self, mock_pipe):
        """Verifica se o sistema usa o pipeline padrão se a aceleração estiver desligada."""
        config = self.config.copy()
        config["acceleration"]["enabled"] = False

        FileProcessor(config)

        # Deve chamar o pipeline padrão do transformers
        self.assertTrue(mock_pipe.called)


if __name__ == "__main__":
    unittest.main()
