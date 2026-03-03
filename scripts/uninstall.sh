#!/bin/bash


cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
NC='\033[0m'


if [ ! -f "src/smartsort/__main__.py" ]; then
    echo -e "${VERMELHO}ERRO CRÍTICO: Não foi possível validar a raiz do projeto SmartSort em $ROOT_DIR.${NC}"
    echo "A desinstalação foi abortada por segurança para evitar apagar ficheiros incorretos."
    exit 1
fi

echo -e "${AMARELO}Bem-vindo ao desinstalador do SmartSort! (Diretório: $ROOT_DIR)${NC}"


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


remover_venv() {
    echo "A remover o ambiente virtual (venv)..."
    if [ -d "$ROOT_DIR/venv" ]; then
        rm -rf "$ROOT_DIR/venv"
        echo -e "${VERDE}Ambiente virtual removido.${NC}"
    fi
}


remover_config() {
    read -p "Deseja remover as configurações em config/config.yaml? [s/N]: " remover
    if [[ "$remover" == "s" || "$remover" == "S" ]]; then
        if [ -d "$ROOT_DIR/config" ]; then
            rm -rf "$ROOT_DIR/config"
            echo -e "${VERDE}Configurações removidas.${NC}"
        fi
    fi
}


remover_dados() {
    echo -e "${AMARELO}AVISO: A pasta de dados ordenados (data/sorted) contém os seus ficheiros organizados.${NC}"
    read -p "Deseja remover DEFINITIVAMENTE a pasta data/sorted? [s/N]: " remover
    if [[ "$remover" == "s" || "$remover" == "S" ]]; then
        if [ -d "$ROOT_DIR/data/sorted" ]; then
            rm -rf "$ROOT_DIR/data/sorted"
            echo -e "${VERDE}Pasta de dados ordenados removida.${NC}"
        fi
    fi
}


read -p "Tem a certeza que deseja desinstalar o SmartSort? [s/N]: " confirmar
if [[ "$confirmar" == "s" || "$confirmar" == "S" ]]; then
    remover_servico
    remover_venv
    remover_config
    remover_dados
    echo -e "${VERDE}Desinstalação concluída!${NC}"
    echo "Nota: O código fonte em $(pwd) não foi removido. Pode apagá-lo manualmente se desejar."
else
    echo "Desinstalação abortada."
fi
