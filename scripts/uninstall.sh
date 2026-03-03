#!/bin/bash

# Deteta a pasta real do script e a raiz do projeto
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

cd "$PROJECT_ROOT"

VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
NC='\033[0m'

if [ ! -f "src/smartsort/__main__.py" ]; then
    echo -e "${VERMELHO}ERRO CRÍTICO: Não foi possível validar a raiz do projeto SmartSort em $PROJECT_ROOT.${NC}"
    echo "A desinstalação foi abortada por segurança para evitar apagar ficheiros incorretos."
    exit 1
fi

echo -e "${AMARELO}Bem-vindo ao desinstalador do SmartSort! (Diretório: $PROJECT_ROOT)${NC}"

remover_servico() {
    echo "A remover o serviço systemd..."
    if [ -f "/etc/systemd/system/smartsort.service" ]; then
        sudo systemctl stop smartsort.service
        sudo systemctl disable smartsort.service
        sudo rm /etc/systemd/system/smartsort.service
        sudo systemctl daemon-reload
        echo -e "${VERDE}Serviço systemd removido com sucesso.${NC}"
    else
        echo "Serviço systemd não encontrado ou já removido."
    fi
}

remover_atalho_cli() {
    echo "A remover o atalho global da CLI..."
    if [ -L "/usr/local/bin/smartsort" ]; then
        sudo rm /usr/local/bin/smartsort
        echo -e "${VERDE}Atalho global removido.${NC}"
    else
        echo "Atalho global não encontrado."
    fi
}

remover_venv() {
    echo "A remover o ambiente virtual (venv)..."
    if [ -d "$PROJECT_ROOT/venv" ]; then
        rm -rf "$PROJECT_ROOT/venv"
        echo -e "${VERDE}Ambiente virtual removido.${NC}"
    fi
}

remover_config() {
    read -p "Deseja remover as configurações em config/config.yaml? [s/N]: " remover
    if [[ "$remover" == "s" || "$remover" == "S" ]]; then
        if [ -d "$PROJECT_ROOT/config" ]; then
            rm -rf "$PROJECT_ROOT/config"
            echo -e "${VERDE}Configurações removidas.${NC}"
        fi
    fi
}

remover_dados() {
    echo -e "${AMARELO}AVISO: A pasta de dados ordenados (data/sorted) contém os seus ficheiros organizados.${NC}"
    read -p "Deseja remover DEFINITIVAMENTE a pasta data/sorted? [s/N]: " remover
    if [[ "$remover" == "s" || "$remover" == "S" ]]; then
        if [ -d "$PROJECT_ROOT/data/sorted" ]; then
            rm -rf "$PROJECT_ROOT/data/sorted"
            echo -e "${VERDE}Pasta de dados ordenados removida.${NC}"
        fi
    fi
}

read -p "Tem a certeza que deseja desinstalar o SmartSort? [s/N]: " confirmar
if [[ "$confirmar" == "s" || "$confirmar" == "S" ]]; then
    remover_servico
    remover_atalho_cli
    remover_venv
    remover_config
    remover_dados
    echo -e "${VERDE}Desinstalação concluída!${NC}"
    echo "Nota: O código fonte em $PROJECT_ROOT não foi removido. Pode apagá-lo manualmente se desejar."
else
    echo "Desinstalação abortada."
fi
