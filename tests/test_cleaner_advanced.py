import os
import tempfile
import unittest
from unittest.mock import patch

from smartsort.utils.cleaner import main, remove_python_comments


class TestCleanerAdvanced(unittest.TestCase):
    @patch("smartsort.utils.cleaner.logger")
    def test_remove_python_comments_error(self, mock_logger):

        with patch("builtins.open", side_effect=Exception("Read Error")):
            remove_python_comments("non_existent.py")
            mock_logger.error.assert_called()

    @patch("smartsort.utils.cleaner.remove_python_comments")
    @patch("smartsort.utils.cleaner.remove_shell_comments")
    def test_cleaner_main_dir(self, mock_sh, mock_py):
        with tempfile.TemporaryDirectory() as tmpdir:

            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write("print(1)")

            with patch("sys.argv", ["cleaner.py", tmpdir]):
                main()
                mock_py.assert_called()


if __name__ == "__main__":
    unittest.main()
