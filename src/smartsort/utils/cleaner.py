import io
import os
import sys
import tokenize

from rich.console import Console

console = Console()


def _get_python_comments(source: str, filepath: str) -> list:
    comments = []
    try:
        tokens = tokenize.tokenize(io.BytesIO(source.encode("utf-8")).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comments.append((tok.start, tok.end))
    except (tokenize.TokenError, IndentationError):
        pass
    except Exception as e:
        console.print(f"[red]Erro ao processar tokens de Python {filepath}: {e}[/red]")
    return comments


def remove_python_comments(filepath: str) -> None:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        console.print(f"[red]Erro ao ler {filepath}: {e}[/red]")
        return

    comments = _get_python_comments(source, filepath)
    if not comments:
        return

    lines = source.splitlines(keepends=True)
    for start, end in reversed(comments):
        s_row, s_col = start
        e_row, e_col = end
        idx = s_row - 1
        lines[idx] = lines[idx][:s_col].rstrip() + lines[idx][e_col:]

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        console.print(f"[green]INFO[/green]     Comentários removidos (Python): [blue]{filepath}[/blue]")
    except Exception as e:
        console.print(f"[red]Erro ao escrever Python {filepath}: {e}[/red]")


class ShellParser:
    def __init__(self, content: str):
        self.content = content
        self.result = []
        self.in_sq = False
        self.in_dq = False
        self.escape = False
        self.modified = False
        self.i = 0

    def parse(self) -> str:
        while self.i < len(self.content):
            char = self.content[self.i]
            if self.escape:
                self._handle_escape(char)
            elif char == "\\":
                self.escape = True
                self.result.append(char)
                self.i += 1
            elif char == "'" and not self.in_dq:
                self.in_sq = not self.in_sq
                self.result.append(char)
                self.i += 1
            elif char == '"' and not self.in_sq:
                self.in_dq = not self.in_dq
                self.result.append(char)
                self.i += 1
            elif char == "#" and not self.in_sq and not self.in_dq:
                if self._handle_hash():
                    continue
            else:
                self.result.append(char)
                self.i += 1
        return "".join(self.result)

    def _handle_escape(self, char: str) -> None:
        self.result.append(char)
        self.escape = False
        self.i += 1

    def _handle_hash(self) -> bool:
        prev = self.content[self.i - 1] if self.i > 0 else " "
        if prev.isspace() or prev in ";&|()":
            if self.i == 0 and self.content.startswith("#!"):
                return False
            self.modified = True
            pos = self.content.find("\n", self.i)
            while self.result and self.result[-1] in (" ", "\t"):
                self.result.pop()
            if pos == -1:
                self.i = len(self.content)
            else:
                self.i = pos
            return True
        return False


def remove_shell_comments(filepath: str) -> None:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        console.print(f"[red]Erro ao ler {filepath}: {e}[/red]")
        return

    parser = ShellParser(content)
    final = parser.parse()

    if not parser.modified:
        return

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final)
        console.print(f"[green]INFO[/green]     Comentários removidos (Shell): [blue]{filepath}[/blue]")
    except Exception as e:
        console.print(f"[red]Erro ao escrever Shell {filepath}: {e}[/red]")


def process_target(target: str) -> None:
    if os.path.isfile(target):
        if target.endswith(".py"):
            remove_python_comments(target)
        elif target.endswith(".sh"):
            remove_shell_comments(target)
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            for file in files:
                path = os.path.join(root, file)
                if path.endswith(".py"):
                    remove_python_comments(path)
                elif path.endswith(".sh"):
                    remove_shell_comments(path)


def main() -> None:
    if len(sys.argv) < 2:
        console.print("[yellow]Uso: python -m smartsort.utils.cleaner <arquivo_ou_diretorio>[/yellow]")
        sys.exit(1)

    for target in sys.argv[1:]:
        process_target(target)


if __name__ == "__main__":
    main()
