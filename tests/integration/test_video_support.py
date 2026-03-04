from pathlib import Path
from unittest.mock import MagicMock

import pytest

from smartsort.core.engine import FileProcessor
from smartsort.utils.recommender import HardwareRecommender


@pytest.fixture
def video_config(tmp_path):
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    dest_dir = tmp_path / "sorted"
    dest_dir.mkdir()

    return {
        "directories_to_watch": [str(watch_dir)],
        "destination_base_folder": str(dest_dir),
        "ai_classification": {"enabled": True, "mode": "zero_shot"},
        "audio_classification": {
            "enabled": True,
            "ac_mode": {"enabled": True, "model": "tiny", "use_gpu": False},
            "battery_mode": {"enabled": False},
        },
        "power_saving": {"enabled": False},
        "fallback_rules": {"mp4": "Videos_Fallback", "mkv": "Videos_Fallback"},
    }


def test_video_with_audio_classification_integration(video_config, mocker):
    """
    INTEGRAÇÃO: Vídeo + Whisper + ZeroShot
    GIVEN: Um ficheiro de vídeo com áudio transcrevível
    WHEN: O FileProcessor processa o vídeo
    THEN: O áudio é transcrito e a categoria é definida via IA (Finanças)
    """
    watch_dir = Path(video_config["directories_to_watch"][0])
    dest_dir = Path(video_config["destination_base_folder"])

    mock_whisper = MagicMock()
    mock_whisper.transcribe.return_value = {"text": "este é um vídeo sobre finanças e contas"}
    mocker.patch("whisper.load_model", return_value=mock_whisper)

    mock_clf = mocker.Mock()
    mock_clf.return_value = {"labels": ["Financas"], "scores": [0.98]}

    mocker.patch("time.sleep")
    mocker.patch("smartsort.core.engine.FileProcessor._load_models")

    processor = FileProcessor(video_config)
    processor.zero_shot_classifier = mock_clf
    processor.whisper_model = mock_whisper

    video_file = watch_dir / "aula_investimento.mp4"
    video_file.write_text("dummy video content")

    processor.process_file(str(video_file))

    expected = dest_dir / "Financas" / "aula_investimento.mp4"
    assert expected.exists()
    assert mock_whisper.transcribe.called


def test_video_fallback_when_whisper_fails_integration(video_config, mocker):
    """
    INTEGRAÇÃO: Vídeo + Whisper Falha
    GIVEN: Um ficheiro de vídeo onde o Whisper falha ou não transcreve
    WHEN: O FileProcessor processa o vídeo
    THEN: Deve recorrer às fallback_rules por extensão (Videos_Fallback)
    """
    watch_dir = Path(video_config["directories_to_watch"][0])
    dest_dir = Path(video_config["destination_base_folder"])

    mocker.patch("time.sleep")
    mocker.patch("smartsort.core.engine.FileProcessor._load_models")
    mocker.patch("smartsort.core.engine.FileProcessor._load_audio_model")

    processor = FileProcessor(video_config)
    processor.whisper_model = None

    video_file = watch_dir / "filme.mkv"
    video_file.write_text("dummy")

    processor.process_file(str(video_file))

    expected = dest_dir / "Videos_Fallback" / "filme.mkv"
    assert expected.exists()


def test_audio_config_recommendation_logic_unit(mocker):
    """
    UNITÁRIO: HardwareRecommender para Áudio
    GIVEN: Diferentes estados de hardware e energia
    WHEN: recommend_audio_config é chamado
    THEN: Sugere o modelo Whisper adequado (tiny vs base)
    """
    config = {"audio_classification": {"enabled": True}}
    recommender = HardwareRecommender(config)

    mocker.patch("psutil.virtual_memory", return_value=mocker.Mock(total=16 * (1024**3)))
    mocker.patch.object(recommender, "_check_nvidia_gpu", return_value=False)

    rec_ac = recommender.recommend_audio_config(on_battery=False)
    assert rec_ac["model"] == "base"

    rec_batt = recommender.recommend_audio_config(on_battery=True)
    assert rec_batt["model"] == "tiny"
    assert rec_batt["use_gpu"] is False
