#!/bin/bash


VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
NC='\033[0m'

echo "Iniciando testes do script uninstall.sh..."


TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/scripts"
mkdir -p "$TEST_DIR/src/smartsort"
mkdir -p "$TEST_DIR/venv"
mkdir -p "$TEST_DIR/config"
mkdir -p "$TEST_DIR/data/sorted"


touch "$TEST_DIR/src/smartsort/__main__.py"
touch "$TEST_DIR/config/config.yaml"
touch "$TEST_DIR/data/sorted/ficheiro.txt"


MOCK_SYSTEMD_DIR=$(mktemp -d)
touch "$MOCK_SYSTEMD_DIR/smartsort.service"



sed "s|/etc/systemd/system/smartsort.service|$MOCK_SYSTEMD_DIR/smartsort.service|g" scripts/uninstall.sh > "$TEST_DIR/scripts/uninstall.sh"
chmod +x "$TEST_DIR/scripts/uninstall.sh"


sudo() { shift; "$@"; }
systemctl() { echo "MOCK systemctl $@"; }
export -f sudo
export -f systemctl


run_test_in_dir() {
    local input=$1

    (cd "$TEST_DIR" && echo -e "$input" | bash "scripts/uninstall.sh" > /dev/null 2>&1)
}


echo -n "Teste 1: Desinstalação completa (removendo venv, config e dados)... "
run_test_in_dir "s\ns\ns\ns"

if [ ! -d "$TEST_DIR/venv" ] && [ ! -d "$TEST_DIR/config" ] && [ ! -d "$TEST_DIR/data/sorted" ] && [ ! -f "$MOCK_SYSTEMD_DIR/smartsort.service" ]; then
    echo -e "${VERDE}Passou${NC}"
else
    echo -e "${VERMELHO}Falhou${NC}"
fi


mkdir -p "$TEST_DIR/venv" "$TEST_DIR/config" "$TEST_DIR/data/sorted"
touch "$MOCK_SYSTEMD_DIR/smartsort.service"
touch "$TEST_DIR/config/config.yaml"


echo -n "Teste 2: Desinstalação parcial (manter config e dados)... "
run_test_in_dir "s\ns\nn\nn"

if [ ! -d "$TEST_DIR/venv" ] && [ -d "$TEST_DIR/config" ] && [ -d "$TEST_DIR/data/sorted" ]; then
    echo -e "${VERDE}Passou${NC}"
else
    echo -e "${VERMELHO}Falhou${NC}"
fi


rm -rf "$TEST_DIR"
rm -rf "$MOCK_SYSTEMD_DIR"
echo "Testes do desinstalador concluídos!"
