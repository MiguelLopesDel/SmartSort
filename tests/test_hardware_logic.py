import unittest
from unittest.mock import MagicMock, patch
from smartsort.core.engine import FileProcessor

class TestHardwareLogicDecision(unittest.TestCase):
    def setUp(self):
        self.config = {
            'ai_classification': {'enabled': True, 'mode': 'zero_shot'},
            'acceleration': {'enabled': True, 'device': 'gpu'},
            'power_saving': {'enabled': True, 'pause_ai_on_battery': True},
            'fallback_rules': {'pdf': 'Documentos'},
            'destination_base_folder': 'data/sorted'
        }

    @patch('smartsort.core.engine.PowerManager')
    def test_should_skip_ai_on_battery(self, MockPowerManager):
        """Verifica se a lógica de pular IA funciona quando a bateria diz que deve."""
        # Configura o PowerManager para dizer que deve usar fallback
        mock_pm = MockPowerManager.return_value
        mock_pm.should_use_fallback.return_value = True
        
        # Não queremos carregar a IA real no __init__ para este teste
        with patch('transformers.pipeline'):
            processor = FileProcessor(self.config)
            processor.power_manager = mock_pm # Garante que usa o nosso mock
            
            # Testa a classificação
            result = processor.classify_file("test.pdf", "test.pdf")
            
            # Deve retornar o fallback 'Documentos' e NÃO chamar os extratores de texto
            category = result[0] if isinstance(result, tuple) else result
            self.assertEqual(category, "Documentos")
            self.assertTrue(mock_pm.should_use_fallback.called)

    @patch('smartsort.core.engine.PowerManager')
    def test_should_run_ai_on_ac_power(self, MockPowerManager):
        """Verifica se a IA é chamada quando o PowerManager diz que está tudo ok."""
        mock_pm = MockPowerManager.return_value
        mock_pm.should_use_fallback.return_value = False
        
        with patch('transformers.pipeline'):
            processor = FileProcessor(self.config)
            processor.power_manager = mock_pm
            
            # Mockamos o extrator de texto para evitar carregar PDFs reais
            with patch.object(processor, 'extract_text_from_pdf', return_value="texto"):
                # Mockamos o classificador final para retornar algo conhecido
                processor.zero_shot_classifier = MagicMock()
                processor.zero_shot_classifier.return_value = {"labels": ["Financas"], "scores": [0.9]}
                
                result = processor.classify_file("test.pdf", "test.pdf")
                category = result[0] if isinstance(result, tuple) else result
                self.assertEqual(category, "Financas")

    def test_acceleration_logic_initialization(self):
        """Verifica se o sistema tenta carregar o acelerador correto no __init__."""
        with patch('optimum.intel.openvino.OVModelForSequenceClassification.from_pretrained') as mock_ov:
            with patch('transformers.pipeline'):
                # Caso 1: Aceleração Ligada
                FileProcessor(self.config)
                self.assertTrue(mock_ov.called)
                
                # Caso 2: Aceleração Desligada
                mock_ov.reset_mock()
                config_no_accel = self.config.copy()
                config_no_accel['acceleration']['enabled'] = False
                FileProcessor(config_no_accel)
                self.assertFalse(mock_ov.called)

if __name__ == '__main__':
    unittest.main()
