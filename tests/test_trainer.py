import unittest
import os
import shutil
from unittest.mock import patch
from smartsort.core.trainer import treinar_modelo_local

class TestTrainer(unittest.TestCase):
    def setUp(self):
        self.test_model_path = "models/test_model.joblib"
        if os.path.exists("models"):
            shutil.rmtree("models")

    def tearDown(self):
        if os.path.exists("models"):
            shutil.rmtree("models")

    def test_treinar_modelo_local_success(self):
        dados = [
            ("Fatura de luz de Janeiro", "Financas"),
            ("Relatorio de vendas", "Trabalho"),
            ("Contrato de arrendamento", "Pessoal"),
            ("Receita medica", "Saude"),
        ]
        
        treinar_modelo_local(dados, self.test_model_path)
        
        self.assertTrue(os.path.exists(self.test_model_path))

    def test_treinar_modelo_vazio(self):
        treinar_modelo_local([], self.test_model_path)
        self.assertFalse(os.path.exists(self.test_model_path))

if __name__ == "__main__":
    unittest.main()
