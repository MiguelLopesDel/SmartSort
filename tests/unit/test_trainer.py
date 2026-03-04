import os

import joblib
from sklearn.pipeline import Pipeline

from smartsort.core.trainer import treinar_modelo_local


def test_treinar_modelo_local_success(tmp_path):
    """
    GIVEN: Um conjunto de dados de treino válido (texto, categoria)
    WHEN: treinar_modelo_local é executado
    THEN: Um arquivo de modelo .joblib válido é criado e pode ser carregado
    """
    model_file = str(tmp_path / "model.joblib")
    dados = [
        ("fatura de eletricidade conta luz energia", "Financas"),
        ("fatura de eletricidade conta luz energia", "Financas"),
        ("fatura de eletricidade conta luz energia", "Financas"),
        ("relatório mensal de desempenho projeto trabalho", "Trabalho"),
        ("relatório mensal de desempenho projeto trabalho", "Trabalho"),
        ("relatório mensal de desempenho projeto trabalho", "Trabalho"),
        ("receita médica e exames saude hospital", "Saude"),
        ("receita médica e exames saude hospital", "Saude"),
        ("convite para festa de aniversário pessoal amigos", "Pessoal"),
        ("convite para festa de aniversário pessoal amigos", "Pessoal"),
    ]

    treinar_modelo_local(dados, model_file)

    assert os.path.exists(model_file)

    loaded_model = joblib.load(model_file)
    assert isinstance(loaded_model, Pipeline)

    prediction = loaded_model.predict(["conta de luz fatura energia"])[0]
    assert prediction == "Financas"


def test_treinar_modelo_local_empty_data(tmp_path, mocker):
    """
    GIVEN: Uma lista vazia de dados de treino
    WHEN: treinar_modelo_local é executado
    THEN: O treinamento é abortado e nenhum arquivo é criado
    """
    model_file = str(tmp_path / "empty_model.joblib")
    mock_logger = mocker.patch("smartsort.core.trainer.logger.warning")

    treinar_modelo_local([], model_file)

    assert not os.path.exists(model_file)
    assert mock_logger.called
    assert "Nenhum dado de treino" in mock_logger.call_args[0][0]


def test_treinar_modelo_local_creates_directory(tmp_path):
    """
    GIVEN: Um caminho de modelo em um diretório inexistente
    WHEN: treinar_modelo_local é executado
    THEN: O diretório pai é criado automaticamente
    """
    nested_dir = tmp_path / "subdir" / "models"
    model_file = str(nested_dir / "test.joblib")
    dados = [("test", "test")]

    treinar_modelo_local(dados, model_file)

    assert os.path.exists(model_file)
    assert os.path.isdir(str(nested_dir))
