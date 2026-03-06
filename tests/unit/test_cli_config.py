import pytest
import yaml

from smartsort.cli.config import add_directory, load_config, save_config, set_model


@pytest.fixture
def mock_config_file(tmp_path, mocker):
    """
    Cria um arquivo de configuração temporário e mocka o caminho no config.py
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"

    initial_config = {
        "directories_to_watch": ["/home/user/downloads"],
        "ai_classification": {"enabled": True, "mode": "zero_shot", "zero_shot_model": "old/model"},
        "acceleration": {"enabled": False},
        "power_saving": {"enabled": False},
    }

    with open(config_file, "w") as f:
        yaml.safe_dump(initial_config, f)

    mocker.patch("smartsort.cli.config.os.path.join", return_value=str(config_file))

    return config_file, initial_config


@pytest.mark.unit
def test_load_config_success(mock_config_file):
    """
    GIVEN: Um arquivo de configuração válido no disco
    WHEN: load_config é chamado
    THEN: Retorna o dicionário de configuração correto
    """
    config = load_config()
    assert config["ai_classification"]["mode"] == "zero_shot"
    assert "/home/user/downloads" in config["directories_to_watch"]


@pytest.mark.unit
def test_save_config_success(mock_config_file):
    """
    GIVEN: Uma nova configuração alterada
    WHEN: save_config é chamado
    THEN: O arquivo no disco é atualizado corretamente
    """
    config_file, config = mock_config_file
    config["acceleration"]["enabled"] = True

    success = save_config(config)
    assert success is True

    with open(config_file, "r") as f:
        saved_config = yaml.safe_load(f)
    assert saved_config["acceleration"]["enabled"] is True


@pytest.mark.unit
def test_add_directory_new(mock_config_file, mocker):
    """
    GIVEN: Um diretório que ainda não está na lista de vigilância
    WHEN: add_directory é chamado com um caminho válido
    THEN: O diretório é adicionado e a config é salva
    """
    config_file, _ = mock_config_file
    new_dir = "/tmp/new_watch_dir"

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.abspath", return_value=new_dir)

    add_directory(new_dir)

    with open(config_file, "r") as f:
        saved_config = yaml.safe_load(f)
    assert new_dir in saved_config["directories_to_watch"]


@pytest.mark.unit
def test_add_directory_already_exists(mock_config_file, mocker):
    """
    GIVEN: Um diretório que JÁ está na lista de vigilância
    WHEN: add_directory é chamado
    THEN: O diretório NÃO é duplicado e um aviso é logado
    """
    _, config = mock_config_file
    existing_dir = config["directories_to_watch"][0]

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.abspath", return_value=existing_dir)
    mock_logger = mocker.patch("smartsort.cli.config.logger.warning")

    add_directory(existing_dir)

    assert mock_logger.called
    assert "já está sendo vigiado" in mock_logger.call_args[0][0]


@pytest.mark.unit
def test_set_model_updates_mode(mock_config_file):
    """
    GIVEN: Um novo nome de modelo
    WHEN: set_model é chamado
    THEN: O modo é alterado para zero_shot e o modelo é atualizado
    """
    config_file, _ = mock_config_file
    new_model = "hf/new-powerful-model"

    set_model(new_model)

    with open(config_file, "r") as f:
        saved_config = yaml.safe_load(f)
    assert saved_config["ai_classification"]["mode"] == "zero_shot"
    assert saved_config["ai_classification"]["zero_shot_model"] == new_model
