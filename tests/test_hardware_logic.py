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
    @patch("smartsort.core.engine.OVModelForSequenceClassification")
    def test_should_skip_ai_on_battery(self, mock_ov, mock_pipe, MockPowerManager):
        """Verifica se a IA é pulada quando a bateria está ativa."""
        mock_pm = MockPowerManager.return_value
        mock_pm.should_use_fallback.return_value = True

        processor = FileProcessor(self.config)
        processor.power_manager = mock_pm

        result = processor.classify_file("test.pdf", "test.pdf")
        category = result[0] if isinstance(result, tuple) else result
        self.assertEqual(category, "Documentos")

    @patch("smartsort.core.engine.pipeline")
    @patch("smartsort.core.engine.OVModelForSequenceClassification")
    def test_cuda_acceleration_selection(self, mock_ov, mock_pipe):
        """Verifica se o provider 'cuda' passa device=0 para o pipeline."""
        config = self.config.copy()
        config["acceleration"]["provider"] = "cuda"

        FileProcessor(config)

        # O pipeline deve ter sido chamado com device=0
        mock_pipe.assert_called()
        # Pega a última chamada se houver várias (ex: OCR + Classificação)
        found_cuda = False
        for call in mock_pipe.call_args_list:
            if call.kwargs.get("device") == 0:
                found_cuda = True
        self.assertTrue(found_cuda, "Pipeline não foi chamado com device=0 para CUDA")

    @patch("smartsort.core.engine.OVModelForSequenceClassification.from_pretrained")
    @patch("smartsort.core.engine.pipeline")
    def test_openvino_acceleration_selection(self, mock_pipe, mock_ov_from_pretrained):
        """Verifica se o provider 'openvino' chama a classe correta do Intel Optimum."""
        config = self.config.copy()
        config["acceleration"]["provider"] = "openvino"
        config["acceleration"]["device"] = "gpu"

        FileProcessor(config)

        mock_ov_from_pretrained.assert_called()
        args, kwargs = mock_ov_from_pretrained.call_args
        self.assertEqual(kwargs.get("device"), "GPU")

    @patch("smartsort.core.engine.OVModelForSequenceClassification.from_pretrained")
    @patch("smartsort.core.engine.pipeline")
    def test_cpu_fallback_logic(self, mock_pipe, mock_ov):
        """Verifica se o sistema usa o pipeline padrão se a aceleração estiver desligada."""
        config = self.config.copy()
        config["acceleration"]["enabled"] = False

        FileProcessor(config)

        # Não deve chamar o OpenVINO
        self.assertFalse(mock_ov.called)
        # Deve chamar o pipeline padrão do transformers
        self.assertTrue(mock_pipe.called)


if __name__ == "__main__":
    unittest.main()
