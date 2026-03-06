# Guia de Contribuição - SmartSort

Obrigado por considerar contribuir para o SmartSort! 🚀

## 🔧 Configuração do Ambiente de Desenvolvimento

### 1. Clone o Repositório

```bash
git clone https://github.com/MiguelLopesDel/SmartSort.git
cd SmartSort
```

### 2. Instale as Dependências de Desenvolvimento

```bash
make install-dev
```

Isso irá:

- Instalar todas as dependências do `requirements-ci.txt`
- Instalar o SmartSort em modo de desenvolvimento
- Configurar os hooks do pre-commit

## ✅ Garantindo Qualidade do Código

### **IMPORTANTE: Evite Erros de Formatação no CI**

Para evitar falhas de formatação no GitHub Actions, **SEMPRE** rode os formatadores antes de fazer push:

```bash
make pre-push
```

Este comando irá:

1. Formatar automaticamente o código com Black e isort
2. Verificar lint (flake8)
3. Verificar tipos (mypy)
4. Rodar os testes

### Comandos Úteis do Makefile

```bash
make format          # Formata o código (Black + isort)
make format-check    # Verifica formatação sem modificar
make lint            # Roda flake8
make type-check      # Roda mypy
make test            # Roda testes
make test-cov        # Roda testes com cobertura
make ci-check        # Roda TODAS as verificações do CI localmente
make clean           # Limpa arquivos de cache
```

### Pre-commit Hooks (Automático)

Após rodar `make install-dev`, os hooks do pre-commit serão executados automaticamente antes de cada commit. Se preferir fazer commit sem os hooks, use:

```bash
git commit --no-verify -m "sua mensagem"
```

**⚠️ ATENÇÃO:** Sempre rode `make pre-push` antes de fazer push, mesmo se pular os hooks!

## 📋 Padrões de Código

### Formatação

- **Black**: Formatador automático de código (line-length: 120)
- **isort**: Organização de imports (perfil: black)
- **flake8**: Verificação de estilo (max-line-length: 120)
- **mypy**: Verificação de tipos estáticos

### ⚠️ Versões FIXAS das Ferramentas

Este projeto usa versões FIXAS das ferramentas de formatação para garantir consistência entre desenvolvimento local e CI:

- `black==24.1.1`
- `isort==5.13.2`
- `flake8==7.0.0`

**NÃO** instale versões diferentes! Use sempre `make install-dev` ou `pip install -r requirements-ci.txt`.

## 🔄 Workflow de Desenvolvimento

1. **Crie uma branch**

    ```bash
    git checkout -b feature/minha-feature
    ```

2. **Desenvolva e teste**

    ```bash
    # Durante o desenvolvimento
    make test
    ```

3. **Formate e verifique**

    ```bash
    # Antes de fazer commit
    make pre-push
    ```

4. **Commit e Push**

    ```bash
    git add .
    git commit -m "feat: minha nova feature"
    git push origin feature/minha-feature
    ```

5. **Abra um Pull Request**

## 🧪 Testes

### Estrutura de Testes

```
tests/
├── unit/           # Testes unitários
├── integration/    # Testes de integração
├── smoke/          # Testes de smoke
└── e2e/            # Testes end-to-end
```

### Rodando Testes

```bash
# Todos os testes
make test

# Com cobertura
make test-cov

# Teste específico
pytest tests/unit/test_engine.py -v

# Teste específico com debug
pytest tests/unit/test_engine.py::test_function_name -vv -s
```

## 📝 Convenções de Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudanças na documentação
- `test:` Adição ou correção de testes
- `refactor:` Refatoração de código
- `perf:` Melhorias de performance
- `ci:` Mudanças no CI/CD
- `chore:` Tarefas de manutenção

Exemplo:

```bash
git commit -m "feat: adiciona suporte para arquivos MKV"
git commit -m "fix: corrige erro de encoding em PDFs"
```

## 🐛 Reportando Bugs

1. Verifique se o bug já foi reportado nas [Issues](https://github.com/MiguelLopesDel/SmartSort/issues)
2. Crie uma nova issue com:
    - Descrição clara do problema
    - Passos para reproduzir
    - Comportamento esperado vs atual
    - Ambiente (OS, Python version, etc.)
    - Logs de erro (se aplicável)

## 💡 Sugerindo Melhorias

1. Abra uma [Issue](https://github.com/MiguelLopesDel/SmartSort/issues) descrevendo:
    - O problema atual
    - Solução proposta
    - Benefícios da mudança
    - Possíveis desvantagens

## ❓ Dúvidas

- Abra uma [Discussion](https://github.com/MiguelLopesDel/SmartSort/discussions)
- Entre em contato através das Issues

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença do projeto (MIT License).

---

**Obrigado por contribuir! 🎉**
