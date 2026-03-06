#!/bin/bash
# Pre-push hook para garantir qualidade do código antes de push
# Para instalar: cp scripts/pre-push.sh .git/hooks/pre-push && chmod +x .git/hooks/pre-push

set -e

echo "🔍 Executando verificações antes do push..."
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar se as ferramentas estão instaladas
if ! command_exists black || ! command_exists isort || ! command_exists flake8; then
    echo -e "${RED}❌ Ferramentas de CI não encontradas!${NC}"
    echo ""
    echo "Execute: make install-dev"
    echo ""
    exit 1
fi

# Verificar versões corretas
echo "📦 Verificando versões das ferramentas..."
BLACK_VERSION=$(black --version | grep -oP 'black, \K[0-9.]+' | head -1)
ISORT_VERSION=$(isort --version | grep -oP 'VERSION \K[0-9.]+' | head -1)

if [[ "$BLACK_VERSION" != "24.1.1" ]]; then
    echo -e "${YELLOW}⚠️  Versão incorreta do Black: $BLACK_VERSION (esperado: 24.1.1)${NC}"
    echo "Execute: pip install black==24.1.1 --force-reinstall"
fi

if [[ "$ISORT_VERSION" != "5.13.2" ]]; then
    echo -e "${YELLOW}⚠️  Versão incorreta do isort: $ISORT_VERSION (esperado: 5.13.2)${NC}"
    echo "Execute: pip install isort==5.13.2 --force-reinstall"
fi

echo ""
echo "1️⃣  Formatando código com Black..."
if ! black src/ tests/; then
    echo -e "${RED}❌ Erro ao formatar com Black${NC}"
    exit 1
fi

echo ""
echo "2️⃣  Organizando imports com isort..."
if ! isort src/ tests/; then
    echo -e "${RED}❌ Erro ao organizar imports${NC}"
    exit 1
fi

echo ""
echo "3️⃣  Verificando estilo com flake8..."
if ! flake8 src/ tests/; then
    echo -e "${RED}❌ Erros de estilo encontrados${NC}"
    exit 1
fi

echo ""
echo "4️⃣  Verificando tipos com mypy..."
if command_exists mypy; then
    if ! mypy src/; then
        echo -e "${YELLOW}⚠️  Avisos do mypy (não bloqueante)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  mypy não encontrado, pulando...${NC}"
fi

echo ""
echo "5️⃣  Executando testes..."
if command_exists pytest; then
    if ! pytest --tb=short -q; then
        echo -e "${RED}❌ Testes falharam${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  pytest não encontrado, pulando testes...${NC}"
fi

echo ""
echo -e "${GREEN}✅ Todas as verificações passaram!${NC}"
echo -e "${GREEN}🚀 Seguro para fazer push!${NC}"
echo ""

exit 0
