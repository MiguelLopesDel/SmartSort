#!/bin/bash

# Encontra o diretório onde o script está localizado
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Verifica se o ambiente virtual existe
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Erro: Ambiente virtual não encontrado em $SCRIPT_DIR/venv"
    echo "Por favor, execute o instalador primeiro: ./scripts/install.sh"
    exit 1
fi

# Ativa o venv e executa a CLI passando todos os argumentos
export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR/src
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/src/smartsort/cli/config.py" "$@"
