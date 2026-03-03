#!/bin/bash

# Mudar para a raiz do projeto
cd "$(dirname "$0")/.."

VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
NC='\033[0m'

echo -e "${AMARELO}Bem-vindo ao desinstalador do SmartSort!${NC}"

# 1. Remover o Serviço Systemd
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

# 2. Remover o Ambiente Virtual
remover_venv() {
    echo "A remover o ambiente virtual (venv)..."
    if [ -d "venv" ]; then
        rm -rf venv
        echo -e "${VERDE}Ambiente virtual removido.${NC}"
    else
        echo "Ambiente virtual não encontrado."
    fi
}

# 3. Remover Configurações (Opcional)
remover_config() {
    read -p "Deseja remover as configurações em config/config.yaml? [s/N]: " remover
    if [[ "$remover" == "s" || "$remover" == "S" ]]; then
        rm -rf config/
        echo -e "${VERDE}Configurações removidas.${NC}"
    fi
}

# 4. Remover Dados Ordenados (Opcional)
remover_dados() {
    read -p "Deseja remover a pasta de ficheiros ordenados (data/sorted)? [s/N]: " remover
    if [[ "$remover" == "s" || "$remover" == "S" ]]; then
        rm -rf data/sorted/
        echo -e "${VERDE}Pasta de dados ordenados removida.${NC}"
    fi
}

# Execução Principal
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
