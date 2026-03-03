#!/bin/bash

# Este script é um wrapper para a CLI do SmartSort.
# Ele resolve caminhos absolutos para funcionar mesmo quando chamado via link simbólico.

# Resolve o caminho real do script (mesmo que seja um symlink)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
PROJECT_ROOT="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Verifica se o ambiente virtual existe
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Erro: Ambiente virtual não encontrado em $PROJECT_ROOT/venv"
    echo "Por favor, execute o instalador primeiro: ./scripts/install.sh"
    exit 1
fi

# Ativa o venv e executa a CLI passando todos os argumentos
export PYTHONPATH=$PYTHONPATH:$PROJECT_ROOT/src
source "$PROJECT_ROOT/venv/bin/activate"
python3 "$PROJECT_ROOT/src/smartsort/cli/config.py" "$@"
