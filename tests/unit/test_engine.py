import shutil
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from smartsort.core.engine import FileProcessor


@pytest.fixture
def config(tmp_path):
    dest_dir = tmp_path / "sorted"
    dest_dir.mkdir()
    return {
        "ai_classification": {"enabled": False},
        "power_saving": {"enabled": False},
        "destination_base_folder": str(dest_dir),
        "fallback_rules": {"pdf": "Documentos", "jpg": "Imagens", "txt": "Textos"},
    }


@pytest.fixture
def processor(config, mocker):

    mocker.patch("smartsort.core.engine.FileProcessor._load_models")

    mocker.patch("smartsort.core.engine.PowerManager")
    mocker.patch("smartsort.core.engine.HardwareRecommender")

    mocker.patch("time.sleep")

    return FileProcessor(config)


@pytest.mark.parametrize(
    "category_in, expected",
    [
        ("Finanças", "Finanças"),
        ("Trabalho/Projeto", "TrabalhoProjeto"),
        ("  Espaços  ", "Espaços"),
        ("Special!@#$%^&*()Chars", "SpecialChars"),
        ("", "Desconhecido"),
        (None, "Desconhecido"),
        ("...", "Desconhecido"),
    ],
)
def test_sanitize_category_parametrized(processor, category_in, expected):
    """
    GIVEN: Nomes de categoria crus, potencialmente com caracteres inválidos
    WHEN: sanitize_category é chamado
    THEN: Retorna um nome de pasta seguro e limpo
    """
    assert processor.sanitize_category(category_in) == expected


def test_process_file_normal_flow(processor, tmp_path, mocker):
    """
    GIVEN: Um arquivo PDF válido em uma pasta monitorada
    WHEN: process_file é chamado
    THEN: O arquivo é movido para a pasta de destino correta baseada no fallback
    """
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    file_path = watch_dir / "doc.pdf"
    file_path.write_text("dummy content")

    mocker.patch.object(processor, "classify_file", return_value=("Documentos", None))

    processor.process_file(str(file_path))

    expected_path = Path(processor.destination_base) / "Documentos" / "doc.pdf"
    assert not file_path.exists()
    assert expected_path.exists()


def test_process_file_handles_collision(processor, tmp_path, mocker):
    """
    GIVEN: Um arquivo cujo nome já existe no destino
    WHEN: process_file é chamado
    THEN: O arquivo é movido com um sufixo de timestamp para evitar sobrescrita
    """
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    file_path = watch_dir / "collision.txt"
    file_path.write_text("new content")

    dest_category_dir = Path(processor.destination_base) / "Textos"
    dest_category_dir.mkdir()
    existing_file = dest_category_dir / "collision.txt"
    existing_file.write_text("old content")

    mocker.patch.object(processor, "classify_file", return_value=("Textos", None))
    mocker.patch("time.time", return_value=123456789)

    processor.process_file(str(file_path))

    expected_path = dest_category_dir / "collision_123456789000.txt"
    assert expected_path.exists()
    assert existing_file.read_text() == "old content"
    assert expected_path.read_text() == "new content"


def test_process_file_ignores_temporary_and_hidden(processor, tmp_path, mocker):
    """
    GIVEN: Arquivos temporários (.tmp, .part) ou ocultos (.hidden)
    WHEN: process_file é chamado
    THEN: Os arquivos são ignorados e NÃO movidos
    """
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()

    tmp_file = watch_dir / "download.part"
    tmp_file.write_text("...")
    hidden_file = watch_dir / ".config"
    hidden_file.write_text("...")

    move_spy = mocker.spy(shutil, "move")

    processor.process_file(str(tmp_file))
    processor.process_file(str(hidden_file))

    assert tmp_file.exists()
    assert hidden_file.exists()
    assert move_spy.call_count == 0


def test_process_file_shutil_move_error_handling(processor, tmp_path, mocker):
    """
    GIVEN: Uma falha catastrófica ao mover o arquivo (ex: permissão negada)
    WHEN: process_file é chamado
    THEN: O erro é capturado e registrado, sem interromper o sistema
    """
    file_path = tmp_path / "locked.pdf"
    file_path.write_text("...")

    mocker.patch.object(processor, "classify_file", return_value=("Docs", None))
    mocker.patch("shutil.move", side_effect=PermissionError("Acesso negado"))
    mock_logger = mocker.patch("smartsort.core.engine.logger.exception")

    processor.process_file(str(file_path))

    assert mock_logger.called
    assert "Erro ao processar" in mock_logger.call_args[0][0]


def test_extract_text_from_pdf_success(processor, mocker):
    """
    GIVEN: Um PDF com texto extraível
    WHEN: extract_text_from_pdf é chamado
    THEN: Retorna o texto extraído formatado
    """
    mock_reader = mocker.patch("smartsort.core.engine.pypdf.PdfReader")
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Texto da Página"
    mock_reader.return_value.pages = [mock_page]

    with patch("builtins.open", mock_open()):
        text = processor.extract_text_from_pdf("test.pdf")
        assert text == "Texto da Página"
