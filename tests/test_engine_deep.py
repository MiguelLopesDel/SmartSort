import unittest
from unittest.mock import patch

from smartsort.core.engine import FileProcessor


class TestEngineDeep(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ai_classification": {"enabled": False},
            "destination_base_folder": "data/sorted",
            "fallback_rules": {},
        }
        self.processor = FileProcessor(self.config)

    def test_sanitize_category(self):

        self.assertEqual(self.processor.sanitize_category("Trabalho/Projeto"), "TrabalhoProjeto")
        self.assertEqual(self.processor.sanitize_category("  Finanças  "), "Finanças")
        self.assertEqual(self.processor.sanitize_category(""), "Desconhecido")
        self.assertEqual(self.processor.sanitize_category(None), "Desconhecido")

    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_log_history(self, mock_file):

        self.processor.log_history("test.pdf", "Financas", "/data/sorted/Financas/test.pdf", 0.95)
        mock_file.assert_called()
        args, kwargs = mock_file().write.call_args
        self.assertIn("Financas", args[0])
        self.assertIn("0.95", args[0])

    @patch("smartsort.core.engine.logger")
    def test_extract_text_pdf_corrupt(self, mock_logger):

        with patch("pypdf.PdfReader", side_effect=Exception("Corrupt")):
            res = self.processor.extract_text_from_pdf("corrupt.pdf")
            self.assertEqual(res, "")
            mock_logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()
