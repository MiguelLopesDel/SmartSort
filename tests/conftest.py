import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_workspace():
    """Cria um diretório temporário para testes e limpa depois."""
    test_dir = tempfile.mkdtemp()
    dest_dir = tempfile.mkdtemp()
    yield test_dir, dest_dir
    shutil.rmtree(test_dir, ignore_errors=True)
    shutil.rmtree(dest_dir, ignore_errors=True)


@pytest.fixture
def mock_base_config():
    """Retorna uma configuração base mínima."""
    return {
        "directories_to_watch": [],
        "destination_base_folder": "/tmp/sorted",
        "ai_classification": {"enabled": False, "mode": "zero_shot"},
        "audio_classification": {"enabled": False},
        "power_saving": {"enabled": False},
        "acceleration": {"enabled": False},
        "fallback_rules": {"txt": "Textos", "pdf": "Documentos"},
    }
