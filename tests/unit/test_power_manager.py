from unittest.mock import MagicMock, mock_open

import pytest

from smartsort.utils.power import PowerManager


@pytest.fixture
def config():
    return {
        "power_saving": {
            "enabled": True,
            "pause_ai_on_battery": True,
            "throttle_interval_sec": 10,
            "stop_below_percent": 20,
        }
    }


@pytest.fixture
def pm(config):
    return PowerManager(config)


@pytest.mark.unit
def test_is_on_battery_scenarios(pm, mocker):
    """
    GIVEN: Diferentes estados de conexão de energia
    WHEN: is_on_battery é chamado
    THEN: Retorna True apenas se houver bateria e não estiver carregando
    """

    mock_battery = mocker.patch("psutil.sensors_battery")
    mock_battery.return_value = MagicMock(power_plugged=False)
    assert pm.is_on_battery() is True

    mock_battery.return_value = MagicMock(power_plugged=True)
    assert pm.is_on_battery() is False

    mock_battery.return_value = None
    assert pm.is_on_battery() is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "percent, expected_percent",
    [
        (50.0, 50.0),
        (15.5, 15.5),
        (None, 100.0),
    ],
)
def test_get_battery_percent_parametrized(pm, mocker, percent, expected_percent):
    """
    GIVEN: Diferentes níveis de bateria informados pelo sistema
    WHEN: get_battery_percent é chamado
    THEN: Retorna o valor correto ou fallback de 100%
    """
    mock_battery = mocker.patch("psutil.sensors_battery")
    if percent is None:
        mock_battery.return_value = None
    else:
        mock_battery.return_value = MagicMock(percent=percent)

    assert pm.get_battery_percent() == expected_percent


@pytest.mark.unit
def test_should_stop_processing_logic(pm, mocker):
    """
    GIVEN: Níveis de bateria críticos ou seguros
    WHEN: should_stop_processing é chamado
    THEN: Retorna True se na bateria e abaixo do limite configurado (20%)
    """
    mock_battery = mocker.patch("psutil.sensors_battery")

    mock_battery.return_value = MagicMock(power_plugged=True, percent=10)
    assert pm.should_stop_processing() is False

    mock_battery.return_value = MagicMock(power_plugged=False, percent=25)
    assert pm.should_stop_processing() is False

    mock_battery.return_value = MagicMock(power_plugged=False, percent=15)
    assert pm.should_stop_processing() is True


@pytest.mark.unit
def test_get_process_resource_usage_error_handling(pm, mocker):
    """
    GIVEN: Falha ao acessar informações do processo (ex: permissão ou PID inexistente)
    WHEN: get_process_resource_usage é chamado
    THEN: Retorna (0.0, 0.0) graciosamente em vez de quebrar
    """
    pm.process = MagicMock()
    pm.process.cpu_percent.side_effect = Exception("Acesso Negado")

    cpu, mem = pm.get_process_resource_usage()
    assert cpu == 0.0
    assert mem == 0.0


@pytest.mark.unit
def test_get_system_discharge_rate_no_sys_fs(pm, mocker):
    """
    GIVEN: Sistema sem /sys/class/power_supply (ex: Windows, WSL, Docker)
    WHEN: get_system_discharge_rate é chamado
    THEN: Retorna None
    """
    mocker.patch("os.path.exists", return_value=False)
    assert pm.get_system_discharge_rate() is None


@pytest.mark.unit
def test_get_system_discharge_rate_linux_success(pm, mocker):
    """
    GIVEN: Sistema Linux com bateria BAT0 reportando power_now
    WHEN: get_system_discharge_rate é chamado
    THEN: Retorna o valor em Watts (uW / 1.000.000)
    """
    mocker.patch("os.path.exists", side_effect=lambda p: True)
    mocker.patch("os.listdir", return_value=["BAT0"])

    m_open = mocker.patch("builtins.open", mock_open())
    m_open.side_effect = [mock_open(read_data="Battery").return_value, mock_open(read_data="15000000").return_value]

    rate = pm.get_system_discharge_rate()
    assert rate == 15.0


@pytest.mark.unit
def test_estimate_app_impact_cpu_zero(pm, mocker):
    """
    GIVEN: Sistema com CPU em repouso absoluto (0% uso total)
    WHEN: estimate_app_impact é chamado
    THEN: Retorna 0.0 em vez de causar divisão por zero
    """
    mocker.patch.object(pm, "is_on_battery", return_value=True)
    mocker.patch.object(pm, "get_process_resource_usage", return_value=(5.0, 100.0))
    mocker.patch("psutil.cpu_percent", return_value=0.0)

    assert pm.estimate_app_impact() == 0.0


@pytest.mark.unit
def test_should_use_fallback_config_disabled(pm):
    """
    GIVEN: Recurso de economia de energia desabilitado na config
    WHEN: should_use_fallback é chamado
    THEN: Sempre retorna False
    """
    pm.config["enabled"] = False
    assert pm.should_use_fallback() is False
