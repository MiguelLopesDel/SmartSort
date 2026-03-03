import unittest
import os
import tempfile
from smartsort.utils.cleaner import remove_python_comments, remove_shell_comments

class TestCleaner(unittest.TestCase):
    def test_remove_python_comments(self):
        content = """# Comentario inicial
def hello(): # Comentario fim de linha
    print("Mundo") # Outro
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            remove_python_comments(temp_path)
            with open(temp_path, 'r') as f:
                new_content = f.read()
            
            self.assertNotIn("# Comentario inicial", new_content)
            self.assertNotIn("# Comentario fim de linha", new_content)
            self.assertIn('print("Mundo")', new_content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_remove_shell_comments(self):
        content = """#!/bin/bash
# Comentario shell
echo "Olá" # Comentario fim
echo "Preço #1" # Nao deve remover o #1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(content)
            temp_path = f.name
            
        try:
            remove_shell_comments(temp_path)
            with open(temp_path, 'r') as f:
                new_content = f.read()
            
            self.assertIn("#!/bin/bash", new_content)
            self.assertNotIn("# Comentario shell", new_content)
            self.assertIn('echo "Preço #1"', new_content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
