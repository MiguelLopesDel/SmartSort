import os
import sys
from rich.console import Console
from rich.table import Table

console = Console()

EXTENSIONS = {'.py', '.sh', '.yaml', '.yml', '.md', '.toml', '.service', '.txt'}
EXCLUDE_DIRS = {
    'venv', 'test_env', '.git', '__pycache__', 'data', 
    '.pytest_cache', '.devcontainer', '.github', 'models', 'dist', 'build'
}

def count_lines(filepath):
    total = 0
    code = 0
    blank = 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total += 1
                if not line.strip():
                    blank += 1
                else:
                    code += 1
    except Exception:
        pass
    return total, code, blank

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    stats = []
    grand_total = 0
    grand_code = 0
    grand_blank = 0

    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for f in filenames:
            ext = os.path.splitext(f)[1]
            if ext in EXTENSIONS or f == 'Dockerfile':
                path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(path, project_root)
                
                t, c, b = count_lines(path)
                stats.append((rel_path, t, c, b))
                
                grand_total += t
                grand_code += c
                grand_blank += b

    stats.sort(key=lambda x: x[2], reverse=True)

    table = Table(title="📊 Estatísticas de Linhas do Projeto", show_footer=True)
    table.add_column("Arquivo", footer="TOTAL")
    table.add_column("Total", justify="right", footer=str(grand_total))
    table.add_column("Código", justify="right", style="green", footer=str(grand_code))
    table.add_column("Vazias", justify="right", style="dim", footer=str(grand_blank))

    for s in stats[:20]:
        table.add_row(s[0], str(s[1]), str(s[2]), str(s[3]))

    if len(stats) > 20:
        table.add_row("...", "...", "...", "...")

    console.print(table)
    
    if grand_total > 0:
        eff = (grand_code / grand_total) * 100
        console.print(f"\n[bold blue]Densidade de Código:[/bold blue] {eff:.1f}%")

if __name__ == "__main__":
    main()
