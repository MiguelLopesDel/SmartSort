from unittest.mock import patch

import pytest

from smartsort.utils.cleaner import main, remove_python_comments, remove_shell_comments


@pytest.mark.unit
@pytest.mark.parametrize(
    "content, expected",
    [
        (
            "def hello():\n    # Isso é um comentário\n    print('oi') # Comentário lateral\n",
            "def hello():\n\n    print('oi')\n",
        ),
        ('print("# not a comment")', 'print("# not a comment")'),
        ("# só comentário", ""),
        ("", ""),
        ("def foo():\n    '''docstring'''\n    pass", "def foo():\n    '''docstring'''\n    pass"),
        ("x = 1  # comment\ny = 2", "x = 1\ny = 2"),
        ("'''multi-line\ndocstring'''\n# comment\nx = 1", "'''multi-line\ndocstring'''\n\nx = 1"),
    ],
)
def test_python_comment_removal_parametrized(tmp_path, content, expected):
    """
    GIVEN: Arquivo Python com variados tipos de comentários e strings
    WHEN: remove_python_comments é chamado
    THEN: Apenas comentários (#) são removidos, preservando a lógica e docstrings
    """
    file = tmp_path / "test.py"
    file.write_text(content, encoding="utf-8")

    remove_python_comments(str(file))

    assert file.read_text(encoding="utf-8") == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "content, expected",
    [
        ("#!/bin/bash\necho 'test' # comentario\n# linha inteira\n", "#!/bin/bash\necho 'test'\n\n"),
        ('echo "# not a comment"', 'echo "# not a comment"'),
        ("echo '# also not a comment'", "echo '# also not a comment'"),
        ("echo \\# not a comment", "echo \\# not a comment"),
        ("# just a comment", ""),
        ("", ""),
        ("ls -la # list files\ncd /tmp # change dir", "ls -la\ncd /tmp"),
    ],
)
def test_shell_comment_removal_parametrized(tmp_path, content, expected):
    """
    GIVEN: Script shell com comentários, strings e escapes
    WHEN: remove_shell_comments é chamado
    THEN: Comentários são removidos, preservando shebangs e strings
    """
    file = tmp_path / "test.sh"
    file.write_text(content, encoding="utf-8")

    remove_shell_comments(str(file))

    assert file.read_text(encoding="utf-8") == expected


@pytest.mark.unit
def test_cleaner_main_directory_walk(tmp_path):
    """
    GIVEN: Uma estrutura de diretórios com arquivos .py e .sh
    WHEN: O main do cleaner é executado apontando para o diretório
    THEN: Todos os arquivos no diretório e subdiretórios são processados
    """
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    py_file = tmp_path / "test.py"
    sh_file = subdir / "test.sh"

    py_file.write_text("x = 1 # comment", encoding="utf-8")
    sh_file.write_text("ls # comment", encoding="utf-8")

    with patch("sys.argv", ["cleaner.py", str(tmp_path)]):
        main()

    assert py_file.read_text(encoding="utf-8") == "x = 1"
    assert sh_file.read_text(encoding="utf-8") == "ls"


@pytest.mark.unit
def test_cleaner_main_single_file(tmp_path):
    """
    GIVEN: Um único arquivo .py
    WHEN: O main do cleaner é executado apontando para o arquivo
    THEN: O arquivo é processado corretamente
    """
    py_file = tmp_path / "test.py"
    py_file.write_text("x = 1 # comment", encoding="utf-8")

    with patch("sys.argv", ["cleaner.py", str(py_file)]):
        main()

    assert py_file.read_text(encoding="utf-8") == "x = 1"
