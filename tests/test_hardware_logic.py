import unittest
from unittest.mock import patch, MagicMock

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


        mock_pipe.assert_called()
        found_cuda = False
        for call in mock_pipe.call_args_list:
            if call.kwargs.get("device") == 0:
                found_cuda = True
        self.assertTrue(found_cuda, "Pipeline não foi chamado com device=0 para CUDA")

    @patch("smartsort.core.engine.pipeline")
    def test_openvino_acceleration_selection(self, mock_pipe):
        """Verifica se o sistema lida com falha no import do OpenVINO."""
        config = self.config.copy()
        config["acceleration"]["provider"] = "openvino"
        config["acceleration"]["device"] = "gpu"

        original_import = __import__

        def side_effect(name, *args, **kwargs):
            if "optimum.intel.openvino" in name:
                raise ImportError
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=side_effect):
            # No novo código, a exceção é capturada e logada, 
            # e como zero_shot_classifier fica None, o pipeline não é chamado no init
            FileProcessor(config)
            self.assertFalse(mock_pipe.called)

    @patch("smartsort.core.engine.pipeline")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_openvino_cache_loading(self, mock_makedirs, mock_exists, mock_pipe):
        """Verifica se o sistema tenta carregar do cache se ele existir."""
        config = self.config.copy()
        config["acceleration"]["provider"] = "openvino"
        

        mock_exists.return_value = True
        

        mock_ov_class = MagicMock()
        with patch.dict("sys.modules", {"optimum.intel.openvino": mock_ov_class}):
            from optimum.intel.openvino import OVModelForSequenceClassification
            with patch.object(OVModelForSequenceClassification, "from_pretrained") as mock_from:
                FileProcessor(config)
                mock_from.assert_called()
                call_path = mock_from.call_args[0][0]
                self.assertIn("ov_cache", call_path)

    @patch("smartsort.core.engine.pipeline")
    def test_cpu_fallback_logic(self, mock_pipe):
        """Verifica se o sistema usa o pipeline padrão se a aceleração estiver desligada."""
        config = self.config.copy()
        config["acceleration"]["enabled"] = False

        FileProcessor(config)


        self.assertTrue(mock_pipe.called)


if __name__ == "__main__":
    unittest.main()
