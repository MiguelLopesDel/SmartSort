from pathlib import Path

import pytest
import yaml

from smartsort.core.engine import FileProcessor


@pytest.mark.smoke
def test_real_config_validity():
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "config" / "config.yaml"

    assert config_path.exists()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        assert config is not None
        assert "ai_classification" in config


@pytest.mark.smoke
def test_processor_with_minimal_valid_config():
    config = {
        "directories_to_watch": [],
        "destination_base_folder": "/tmp/sorted",
        "ai_classification": {"enabled": False},
        "power_saving": {"enabled": False},
    }
    processor = FileProcessor(config)
    assert processor is not None
