import pytest
import yaml
from typer.testing import CliRunner

import smartsort.cli.config as cli_config
from smartsort.cli.config import app

runner = CliRunner()


@pytest.fixture
def temp_config_env(tmp_path, mocker):
    """
    Prepara um ambiente E2E real com arquivo de configuração no disco.
    """
    config_dir = tmp_path / "config_dir"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.yaml"

    initial_config = {
        "directories_to_watch": [],
        "ai_classification": {"enabled": True, "mode": "zero_shot", "zero_shot_model": "test-model"},
        "acceleration": {"enabled": False, "provider": "auto", "device": "auto"},
        "power_saving": {"enabled": False},
        "destination_base_folder": "data/sorted",
    }

    with open(config_file, "w") as f:
        yaml.safe_dump(initial_config, f)

    def mock_load():
        try:
            with open(config_file, "r") as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def mock_save(config):
        try:
            with open(config_file, "w") as f:
                yaml.safe_dump(config, f)
            return True
        except Exception:
            return False

    mocker.patch("smartsort.cli.config.load_config", side_effect=mock_load)
    mocker.patch("smartsort.cli.config.save_config", side_effect=mock_save)

    return config_file


@pytest.mark.e2e
def test_cli_show_config_e2e(temp_config_env):
    """
    E2E: Garante que o comando 'show' lê e exibe a configuração real do disco.
    """
    result = runner.invoke(app, ["show"])
    assert result.exit_code == 0
    assert "Configuração SmartSort" in result.stdout
    assert "zero_shot" in result.stdout


@pytest.mark.e2e
def test_cli_add_directory_e2e(temp_config_env, tmp_path):
    """
    E2E: Garante que o comando 'add' valida o diretório e persiste no disco.
    """
    watch_dir = tmp_path / "external_watch"
    watch_dir.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["add", str(watch_dir)])
    assert result.exit_code == 0
    assert "Sucesso" in result.stdout

    config = cli_config.load_config()
    assert str(watch_dir) in config["directories_to_watch"]


@pytest.mark.e2e
def test_cli_status_e2e(temp_config_env, mocker):
    """
    E2E: Garante que o comando 'status' exibe informações de hardware/bateria.
    """
    mocker.patch("psutil.sensors_battery", return_value=None)
    mocker.patch("platform.processor", return_value="Generic CPU")

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Status do Sistema" in result.stdout


@pytest.mark.e2e
def test_cli_accel_analysis_e2e(temp_config_env, mocker):
    """
    E2E: Garante que o comando 'accel' executa a análise de hardware.
    """
    mocker.patch("psutil.sensors_battery", return_value=None)
    mocker.patch("platform.processor", return_value="Generic CPU")

    mocker.patch("smartsort.utils.recommender.logger.info")

    result = runner.invoke(app, ["accel"])
    assert result.exit_code == 0
