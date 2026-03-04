import unittest
from unittest.mock import patch

from smartsort.core.engine import FileProcessor


class TestEngineUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {"ai_classification": {"enabled": False}, "power_saving": {"enabled": False}}
        self.processor = FileProcessor(self.config)

    @patch("smartsort.core.engine.pypdf.PdfReader")
    def test_extract_text_from_pdf_error(self, mock_reader) -> None:
        """Garante que falhas na extração de PDF retornam string vazia em vez de crash."""
        mock_reader.side_effect = Exception("Corrupted PDF")

        with patch("builtins.open", new_callable=unittest.mock.mock_open):
            result = self.processor.extract_text_from_pdf("fake.pdf")
            self.assertEqual(result, "")

    @patch("smartsort.core.engine.Image.open")
    @patch("smartsort.core.engine.pytesseract.image_to_string")
    def test_extract_text_from_image_missing_lang(self, mock_tesseract, mock_image) -> None:
        """Testa o tratamento elegante quando o idioma português do Tesseract não está instalado."""
        mock_tesseract.side_effect = Exception("Tesseract não encontrou o idioma 'por'")

        result = self.processor.extract_text_from_image("fake.jpg")
        self.assertEqual(result, "")

    def test_update_config_triggers_reload(self) -> None:
        """Verifica se mudar a configuração forçará o reload dos modelos."""
        with patch.object(self.processor, "_load_models") as mock_load:
            new_config = {
                "ai_classification": {"enabled": True, "mode": "local", "zero_shot_model": "novo_modelo"},
                "power_saving": {"enabled": False},
            }
            self.processor.update_config(new_config)
            mock_load.assert_called_once()

    def test_simulate_ai_classification(self) -> None:
        """Testa o fallback simulado."""
        self.assertEqual(self.processor.simulate_ai_classification("fatura_luz.pdf"), "Financas")
        self.assertEqual(self.processor.simulate_ai_classification("relatorio.docx"), "Trabalho")
        self.assertEqual(self.processor.simulate_ai_classification("ferias.jpg"), "Outros")


if __name__ == "__main__":
    unittest.main()
