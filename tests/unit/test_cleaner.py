import os
import tempfile
import unittest

from smartsort.utils.cleaner import remove_python_comments, remove_shell_comments


class TestCleaner(unittest.TestCase):
    def test_python_comment_removal(self):
        content = "def hello():\n    # Isso é um comentário\n    print('oi') # Comentário lateral\n"

        expected = "def hello():\n\n    print('oi')\n"

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(content)
            tmp_path = f.name

        try:
            remove_python_comments(tmp_path)
            with open(tmp_path, "r") as f:
                result = f.read()
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)

    def test_shell_comment_removal(self):
        content = "#!/bin/bash\necho 'test' # comentario\n# linha inteira\n"

        expected = "#!/bin/bash\necho 'test'\n\n"

        with tempfile.NamedTemporaryFile(suffix=".sh", mode="w", delete=False) as f:
            f.write(content)
            tmp_path = f.name

        try:
            remove_shell_comments(tmp_path)
            with open(tmp_path, "r") as f:
                result = f.read()
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
