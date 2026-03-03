#!/bin/bash

# Cores para o output
VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
NC='\033[0m'

echo "Iniciando testes do script uninstall.sh..."

# 1. Criar ambiente de teste isolado
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/scripts"
mkdir -p "$TEST_DIR/src/smartsort"
mkdir -p "$TEST_DIR/venv"
mkdir -p "$TEST_DIR/config"
mkdir -p "$TEST_DIR/data/sorted"
touch "$TEST_DIR/src/smartsort/__main__.py" # Ficheiro de validação de segurança
touch "$TEST_DIR/config/config.yaml"
touch "$TEST_DIR/data/sorted/ficheiro.txt"

# Criar um ficheiro de serviço falso (mock do systemd)
MOCK_SYSTEMD_DIR=$(mktemp -d)
touch "$MOCK_SYSTEMD_DIR/smartsort.service"

# Copiar o desinstalador para o ambiente de teste e injetar mocks
# Vamos usar o sed para substituir os comandos reais por versões de log
sed "s|/etc/systemd/system/smartsort.service|$MOCK_SYSTEMD_DIR/smartsort.service|g" scripts/uninstall.sh > "$TEST_DIR/scripts/uninstall_testable.sh"
chmod +x "$TEST_DIR/scripts/uninstall_testable.sh"

# Mocks de comandos globais
sudo() { shift; "$@"; }
systemctl() { echo "MOCK systemctl $@"; }
export -f sudo
export -f systemctl

# Função para correr o teste simulando entradas do utilizador
run_test() {
    local input=$1
    # Entrar no diretório de teste para que os comandos rm -rf apaguem as pastas locais simuladas
    (cd "$TEST_DIR" && echo -e "$input" | bash "scripts/uninstall_testable.sh" > /dev/null 2>&1)
}

# Teste 1: Desinstalação completa (Remover tudo)
echo -n "Teste 1: Desinstalação completa (removendo venv, config e dados)... "
run_test "s
s
s
s"

if [ ! -d "$TEST_DIR/venv" ] && [ ! -d "$TEST_DIR/config" ] && [ ! -d "$TEST_DIR/data/sorted" ] && [ ! -f "$MOCK_SYSTEMD_DIR/smartsort.service" ]; then
    echo -e "${VERDE}Passou${NC}"
else
    echo -e "${VERMELHO}Falhou${NC}"
fi

# Reset para Teste 2
mkdir -p "$TEST_DIR/venv" "$TEST_DIR/config" "$TEST_DIR/data/sorted"
touch "$MOCK_SYSTEMD_DIR/smartsort.service"

# Teste 2: Manter dados e config
echo -n "Teste 2: Desinstalação parcial (manter config e dados)... "
run_test "s
s
n
n"

if [ ! -d "$TEST_DIR/venv" ] && [ -d "$TEST_DIR/config" ] && [ -d "$TEST_DIR/data/sorted" ]; then
    echo -e "${VERDE}Passou${NC}"
else
    echo -e "${VERMELHO}Falhou${NC}"
fi

# Limpeza
rm -rf "$TEST_DIR"
rm -rf "$MOCK_SYSTEMD_DIR"
echo "Testes do desinstalador concluídos!"
