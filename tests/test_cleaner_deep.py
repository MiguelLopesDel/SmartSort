import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from smartsort.utils.cleaner import remove_shell_comments, main

class TestCleanerDeep(unittest.TestCase):
    def test_remove_shell_comments_complex(self):

        content = """#!/bin/bash
echo "Isso # não é comentário"
ls # Isso é
VAR="# valor"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(content)
            path = f.name
        
        try:
            remove_shell_comments(path)
            with open(path, 'r') as f:
                new = f.read()
            self.assertIn('echo "Isso # não é comentário"', new)
            self.assertNotIn("Isso é", new)
            self.assertIn('VAR="# valor"', new)
        finally:
            os.remove(path)

    @patch("smartsort.utils.cleaner.logger")
    def test_main_no_args(self, mock_logger):
        with patch("sys.argv", ["cleaner.py"]):
            with self.assertRaises(SystemExit):
                main()
            mock_logger.warning.assert_called()

    @patch("smartsort.utils.cleaner.remove_python_comments")
    def test_main_single_file(self, mock_remove):
        with patch("sys.argv", ["cleaner.py", "test.py"]):
            with patch("os.path.isfile", return_value=True):
                main()
                mock_remove.assert_called_with("test.py")

if __name__ == "__main__":
    unittest.main()
