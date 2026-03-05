from unittest.mock import MagicMock

import pytest

from smartsort.utils.recommender import HardwareRecommender


@pytest.fixture
def recommender():
    return HardwareRecommender(config={})


@pytest.mark.unit
@pytest.mark.parametrize(
    "cpu_brand, has_nvidia, on_battery, expected_provider, expected_device",
    [
        ("Intel(R) Core(TM) i7", False, False, "openvino", "GPU"),
        ("AMD Ryzen 5", False, False, "openvino", "GPU"),
        ("Intel(R) Core(TM) i9", True, False, "cuda", "GPU"),
        ("Intel(R) Core(TM) i5", False, True, "openvino", "GPU"),
        ("AMD Ryzen 7", False, True, "openvino", "CPU"),
        ("Apple M1", False, False, "auto", "CPU"),
        ("Unknown ARM", False, True, "auto", "CPU"),
    ],
)
def test_get_best_acceleration_parametrized(
    recommender, mocker, cpu_brand, has_nvidia, on_battery, expected_provider, expected_device
):
    """
    GIVEN: Diferentes combinações de CPU, GPU e estado de energia
    WHEN: get_best_acceleration é chamado
    THEN: Retorna a melhor recomendação de (provider, device)
    """
    mocker.patch("platform.processor", return_value=cpu_brand)
    mocker.patch.object(recommender, "_check_nvidia_gpu", return_value=has_nvidia)

    provider, device = recommender.get_best_acceleration(on_battery=on_battery)

    assert provider == expected_provider
    assert device == expected_device


@pytest.mark.unit
def test_show_analysis_output_content(recommender, mocker):
    """
    GIVEN: Um cenário de hardware específico
    WHEN: show_analysis é chamado
    THEN: O log deve conter informações detalhadas da análise, não apenas ser chamado
    """
    mocker.patch("platform.processor", return_value="Intel Core i7")
    mocker.patch.object(recommender, "_check_nvidia_gpu", return_value=False)
    mocker.patch("psutil.sensors_battery", return_value=MagicMock(power_plugged=False))

    mock_logger = mocker.patch("smartsort.utils.recommender.logger.info")

    recommender.show_analysis()

    all_logs = "".join([str(call.args[0]) for call in mock_logger.call_args_list])

    assert "ANÁLISE DE HARDWARE" in all_logs
    assert "OPENVINO" in all_logs
    assert "GPU" in all_logs
    assert "Notebook detectado em bateria" in all_logs
    assert "Priorizando eficiência" in all_logs


@pytest.mark.unit
def test_gpu_not_awakened_on_battery(recommender, mocker):
    """
    BUG REPRODUCTION:
    GIVEN: O notebook está em modo bateria (on_battery=True)
    WHEN: get_best_acceleration é chamado
    THEN: _check_nvidia_gpu NÃO deve ser chamado, para evitar acordar a GPU dedicada.
    """
    mocker.patch("platform.processor", return_value="Intel Core i7")
    spy = mocker.spy(recommender, "_check_nvidia_gpu")

    recommender.get_best_acceleration(on_battery=True)

    assert spy.call_count == 0, "ERRO: _check_nvidia_gpu foi chamado em modo bateria, acordando a GPU!"


@pytest.mark.unit
def test_gpu_awakened_on_ac(recommender, mocker):
    """
    GIVEN: O notebook está na tomada (on_battery=False)
    WHEN: get_best_acceleration é chamado
    THEN: _check_nvidia_gpu DEVE ser chamado para verificar disponibilidade de aceleração.
    """
    mocker.patch("platform.processor", return_value="Intel Core i7")
    spy = mocker.spy(recommender, "_check_nvidia_gpu")

    recommender.get_best_acceleration(on_battery=False)

    assert spy.call_count == 1, "ERRO: _check_nvidia_gpu deveria ter sido chamado na tomada!"


@pytest.mark.unit
def test_check_nvidia_gpu_import_error(recommender, mocker):
    """
    GIVEN: Ambiente sem a biblioteca 'torch' instalada
    WHEN: _check_nvidia_gpu é chamado
    THEN: Deve retornar False graciosamente em vez de lançar exceção
    """
    mocker.patch("builtins.__import__", side_effect=ImportError)

    assert recommender._check_nvidia_gpu() is False
