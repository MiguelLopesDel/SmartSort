import os
import tempfile
import unittest
from unittest.mock import patch

from smartsort.core.trainer import treinar_modelo_local


class TestTrainer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.model_file = os.path.join(self.temp_dir, "modelo_teste.joblib")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("smartsort.core.trainer.joblib.dump")
    def test_treinar_modelo_com_dados(self, mock_dump) -> None:
        """Testa se o treinamento tenta salvar o modelo com dados válidos."""
        dados = [("conta de luz", "Financas"), ("reunião de projeto", "Trabalho")]

        treinar_modelo_local(dados, self.model_file)

        mock_dump.assert_called_once()
        args, _ = mock_dump.call_args
        self.assertEqual(args[1], self.model_file)

    @patch("smartsort.core.trainer.joblib.dump")
    def test_treinar_modelo_sem_dados(self, mock_dump) -> None:
        """Testa que o treinamento é abortado se não houver dados."""
        treinar_modelo_local([], self.model_file)
        mock_dump.assert_not_called()


if __name__ == "__main__":
    unittest.main()
