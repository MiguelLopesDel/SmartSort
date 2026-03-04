import pytest

from smartsort.core.engine import FileProcessor


@pytest.fixture
def integration_env(tmp_path):
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    dest_dir = tmp_path / "sorted"
    dest_dir.mkdir()

    config = {
        "directories_to_watch": [str(watch_dir)],
        "destination_base_folder": str(dest_dir),
        "ai_classification": {
            "enabled": True,
            "mode": "zero_shot",
            "categorias_disponiveis": ["Financas", "Trabalho", "Outros"],
        },
        "power_saving": {"enabled": True, "pause_ai_on_battery": True, "stop_below_percent": 20},
        "fallback_rules": {"pdf": "Documentos_Fallback", "txt": "Textos_Fallback"},
    }
    return watch_dir, dest_dir, config


def test_processor_integration_with_power_manager_fallback(integration_env, mocker):
    """
    INTEGRAÇÃO: FileProcessor + PowerManager
    GIVEN: Sistema operando na bateria
    WHEN: Um arquivo é processado
    THEN: Deve usar fallback_rules em vez de IA pesada para economizar energia
    """
    watch_dir, dest_dir, config = integration_env

    mocker.patch("psutil.sensors_battery", return_value=mocker.Mock(power_plugged=False, percent=50))

    mock_pipeline = mocker.patch("smartsort.core.engine.pipeline")
    mocker.patch("time.sleep")

    processor = FileProcessor(config)

    mock_pipeline.reset_mock()

    test_file = watch_dir / "fatura.pdf"
    test_file.write_text("...")

    processor.process_file(str(test_file))

    expected_path = dest_dir / "Documentos_Fallback" / "fatura.pdf"
    assert expected_path.exists()

    assert mock_pipeline.call_count == 0


def test_processor_integration_with_ai_enabled(integration_env, mocker):
    """
    INTEGRAÇÃO: FileProcessor + ZeroShot Classifier
    GIVEN: Sistema na tomada (IA habilitada)
    WHEN: Um arquivo é processado
    THEN: Deve chamar o classificador de IA e mover para a categoria sugerida
    """
    watch_dir, dest_dir, config = integration_env

    mocker.patch("psutil.sensors_battery", return_value=mocker.Mock(power_plugged=True, percent=100))

    mock_pipe_instance = mocker.Mock()
    mock_pipe_instance.return_value = {"labels": ["Financas"], "scores": [0.95]}
    mocker.patch("smartsort.core.engine.pipeline", return_value=mock_pipe_instance)
    mocker.patch("time.sleep")
    mocker.patch("smartsort.core.engine.FileProcessor._load_models")

    processor = FileProcessor(config)
    processor.zero_shot_classifier = mock_pipe_instance

    test_file = watch_dir / "conta_luz.pdf"
    test_file.write_text("...")

    processor.process_file(str(test_file))

    expected_path = dest_dir / "Financas" / "conta_luz.pdf"
    assert expected_path.exists()
    assert mock_pipe_instance.called


def test_process_existing_files_integration(integration_env, mocker):
    """
    INTEGRAÇÃO: Varredura de arquivos existentes
    GIVEN: Múltiplos arquivos já presentes na pasta de vigilância
    WHEN: process_existing_files é chamado
    THEN: Todos os arquivos devem ser processados e movidos
    """
    watch_dir, dest_dir, config = integration_env
    (watch_dir / "file1.txt").write_text("1")
    (watch_dir / "file2.txt").write_text("2")

    mocker.patch("smartsort.core.engine.FileProcessor._load_models")
    mocker.patch("time.sleep")

    processor = FileProcessor(config)
    mocker.patch.object(processor, "classify_file", return_value=("Textos_Fallback", None))

    processor.process_existing_files()

    assert (dest_dir / "Textos_Fallback" / "file1.txt").exists()
    assert (dest_dir / "Textos_Fallback" / "file2.txt").exists()
