
import sys
import os
import tokenize
import io

def remove_python_comments(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")
        return



    comments = []
    try:
        tokens = tokenize.tokenize(io.BytesIO(source.encode('utf-8')).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comments.append((tok.start, tok.end))
    except tokenize.TokenError:
        pass
    except Exception as e:
        print(f"Erro ao processar tokens de Python {filepath}: {e}")
        return

    if not comments:
        return

    lines = source.splitlines(keepends=True)
    

    for start, end in reversed(comments):
        start_row, start_col = start
        end_row, end_col = end
        
        start_idx = start_row - 1
        end_idx = end_row - 1
        
        if start_idx == end_idx:
            line = lines[start_idx]
            before = line[:start_col]
            after = line[end_col:]
            

            if after == '\n' or after == '\r\n' or after == '':
                before = before.rstrip(' \t')
            
            lines[start_idx] = before + after

    final_content = ''.join(lines)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"Comentários removidos (Python): {filepath}")
    except Exception as e:
        print(f"Erro ao escrever Python {filepath}: {e}")

def remove_shell_comments(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")
        return

    result = []
    in_single_quote = False
    in_double_quote = False
    escape_next = False
    
    i = 0
    modified = False
    while i < len(content):
        char = content[i]
        
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue
            
        if char == '\\':
            escape_next = True
            result.append(char)
            i += 1
            continue
            
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            result.append(char)
            i += 1
            continue
            
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            result.append(char)
            i += 1
            continue
            

        if char == '#' and not in_single_quote and not in_double_quote:
            is_start_of_word = (i == 0 or content[i-1].isspace() or content[i-1] in ';&|()')
            if is_start_of_word:

                if i == 0 and content.startswith('#!'):
                    newline_pos = content.find('\n', i)
                    if newline_pos == -1:
                        result.append(content[i:])
                        break
                    else:
                        result.append(content[i:newline_pos])
                        i = newline_pos
                        continue
                else:
                    modified = True
                    newline_pos = content.find('\n', i)
                    

                    while len(result) > 0 and result[-1] in (' ', '\t'):
                        result.pop()

                    if newline_pos == -1:
                        break
                    else:
                        i = newline_pos
                        continue
                    
        result.append(char)
        i += 1
        
    if not modified:
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(''.join(result))
        print(f"Comentários removidos (Shell): {filepath}")
    except Exception as e:
        print(f"Erro ao escrever Shell {filepath}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python remover_comentarios.py <arquivo_ou_diretorio> [arquivo_ou_diretorio...]")
        sys.exit(1)

    targets = sys.argv[1:]
    for target in targets:
        if os.path.isfile(target):
            if target.endswith('.py'):
                remove_python_comments(target)
            elif target.endswith('.sh'):
                remove_shell_comments(target)
            else:
                print(f"Ignorado (extensão não suportada): {target}")
        elif os.path.isdir(target):
            for root, _, files in os.walk(target):
                for file in files:
                    filepath = os.path.join(root, file)
                    if filepath.endswith('.py'):
                        remove_python_comments(filepath)
                    elif filepath.endswith('.sh'):
                        remove_shell_comments(filepath)

if __name__ == "__main__":
    main()