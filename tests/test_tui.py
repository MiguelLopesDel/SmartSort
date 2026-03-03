import unittest
from unittest.mock import patch, MagicMock

class TestTUISmoke(unittest.TestCase):
    def test_tui_is_importable(self):
        """Garante que o módulo TUI não tem erros de sintaxe e pode ser importado."""
        try:

            with patch("smartsort.cli.config.load_config", return_value={"test": True}):
                from smartsort.cli.tui import SmartSortTUI
                self.assertIsNotNone(SmartSortTUI)
        except Exception as e:
            self.fail(f"Falha ao importar TUI (possível erro de sintaxe): {e}")

    def test_tui_header_render(self):
        """Testa se a função de desenho básico funciona."""
        with patch("smartsort.cli.config.load_config", return_value={"test": True}):
            from smartsort.cli.tui import SmartSortTUI
            tui = SmartSortTUI()
            header = tui.draw_header()
            self.assertIn("SmartSort", str(header.renderable))

if __name__ == "__main__":
    unittest.main()
