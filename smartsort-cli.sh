#!/bin/bash





SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
PROJECT_ROOT="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"


if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Erro: Ambiente virtual não encontrado em $PROJECT_ROOT/venv"
    echo "Por favor, execute o instalador primeiro: ./scripts/install.sh"
    exit 1
fi


export PYTHONPATH=$PYTHONPATH:$PROJECT_ROOT/src
source "$PROJECT_ROOT/venv/bin/activate"
python3 "$PROJECT_ROOT/src/smartsort/cli/config.py" "$@"
