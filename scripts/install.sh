#!/bin/bash

# Deteta a pasta real do script e a raiz do projeto
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

cd "$PROJECT_ROOT"

VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
NC='\033[0m'

echo -e "${VERDE}Bem-vindo ao instalador do SmartSort!${NC}"


verificar_atualizacao() {
    echo "Verificando se há atualizações no repositório..."
    if command -v git &> /dev/null && [ -d ".git" ]; then
        git fetch origin main > /dev/null 2>&1
        LOCAL=$(git rev-parse HEAD 2>/dev/null)
        REMOTE=$(git rev-parse origin/main 2>/dev/null)
        
        if [ "$LOCAL" != "$REMOTE" ] && [ -n "$REMOTE" ]; then
            echo -e "${AMARELO}Uma atualização foi encontrada no repositório.${NC}"
            read -p "Deseja baixar a atualização agora? [s/N]: " atualizar
            if [[ "$atualizar" == "s" || "$atualizar" == "S" ]]; then
                echo "Atualizando de forma inteligente para evitar conflitos..."
                
                # Cancela qualquer merge/rebase pendente que esteja travando o git
                git merge --abort > /dev/null 2>&1
                git rebase --abort > /dev/null 2>&1
                
                # Backup do config.yaml do usuário (único arquivo que ele deve mudar)
                if [ -f "config/config.yaml" ]; then
                    cp "config/config.yaml" "config/config.yaml.bak"
                    echo "Backup da configuração criado."
                fi

                # Força a atualização para o estado da origin/main
                if git reset --hard origin/main; then
                    # Restaura o config do usuário
                    if [ -f "config/config.yaml.bak" ]; then
                        mv "config/config.yaml.bak" "config/config.yaml"
                        echo "Configuração pessoal restaurada com sucesso."
                    fi
                    
                    echo -e "${VERDE}Atualização concluída com sucesso.${NC}"
                    echo -e "${VERDE}Reiniciando o instalador...${NC}"
                    exec "$0" "--skip-update"
                else
                    echo -e "${VERMELHO}ERRO: Falha crítica ao resetar o repositório para a versão mais nova.${NC}"
                    echo "Tente rodar: git fetch && git reset --hard origin/main manualmente."
                    exit 1
                fi
            fi
        else
            echo "O repositório já está atualizado."
        fi
    else
         echo "Pulando verificação de atualizações (não é um repo git)."
    fi
}


detectar_distro() {
    if [ -f "/etc/os-release" ]; then
        . "/etc/os-release"
        DISTRO=$ID
        DISTRO_LIKE=$ID_LIKE
    elif [ -f "/usr/lib/os-release" ]; then
        . "/usr/lib/os-release"
        DISTRO=$ID
        DISTRO_LIKE=$ID_LIKE
    else
        echo -e "${VERMELHO}Não foi possível detectar a distribuição Linux.${NC}"
        exit 1
    fi
    
    echo -e "Distribuição detectada: ${VERDE}${PRETTY_NAME}${NC}"
}


detectar_gpu() {
    echo "Detectando hardware de GPU..."
    
    if ! command -v lspci &> /dev/null; then
        echo -e "${AMARELO}Comando lspci não encontrado. Verificação detalhada de GPU ignorada.${NC}"
        echo -e "${VERMELHO}Não foi possível verificar a GPU. O programa precisa de uma GPU dedicada.${NC}"
        echo -e "${VERMELHO}Instale o 'pciutils' e rode o script novamente. Vou resolver isso depois.${NC}"
        exit 1
    fi


    GPU_INFO=$(lspci -nn | grep -E -i "(VGA|3D)")
    
    HAS_DEDICATED=false
    GPU_VENDOR=""
    NVIDIA_DRIVER=""
    

    if echo "$GPU_INFO" | grep -iq "nvidia"; then
        HAS_DEDICATED=true
        GPU_VENDOR="NVIDIA"
        

        if command -v lsmod &> /dev/null; then
            if lsmod | grep -iq "nouveau"; then
                NVIDIA_DRIVER="Nouveau (Código aberto não oficial)"
            elif lsmod | grep -iq "nvidia"; then

                if command -v modinfo &> /dev/null && modinfo nvidia | grep -q "license:.*Dual MIT/GPL"; then
                    NVIDIA_DRIVER="NVIDIA Open (Código aberto oficial)"
                else
                    NVIDIA_DRIVER="NVIDIA Proprietário (Oficial)"
                fi
            else
                NVIDIA_DRIVER="Nenhum driver NVIDIA carregado"
            fi
        else
            NVIDIA_DRIVER="Indisponível (lsmod ausente)"
        fi
        
    elif echo "$GPU_INFO" | grep -iq -E "radeon rx|navi"; then

        HAS_DEDICATED=true
        GPU_VENDOR="AMD Dedicada"
    elif echo "$GPU_INFO" | grep -iq "intel" && echo "$GPU_INFO" | grep -iq "arc"; then
        HAS_DEDICATED=true
        GPU_VENDOR="Intel Dedicada (ARC)"
    else
        GPU_VENDOR="Integrada/Desconhecida"
    fi


    if [ "$HAS_DEDICATED" = false ]; then
        echo -e "${AMARELO}Nenhuma GPU dedicada detectada. O SmartSort usará a CPU/iGPU.${NC}"
        return 0
    fi

    echo -e "GPU Dedicada detectada: ${VERDE}${GPU_VENDOR}${NC}"
    
    if [ "$GPU_VENDOR" = "NVIDIA" ]; then
        echo -e "Driver NVIDIA em uso: ${AMARELO}${NVIDIA_DRIVER}${NC}"
        if [[ "$NVIDIA_DRIVER" == *"Nouveau"* ]]; then
            echo -e "${AMARELO}AVISO: Você está usando o driver Nouveau! O suporte a aceleração de IA (CUDA) geralmente não funciona ou é muito limitado com este driver.${NC}"
            echo -e "Recomenda-se fortemente a instalação dos drivers oficiais (Proprietário ou Open Oficial) fornecidos pela NVIDIA."
            read -p "Deseja continuar com a instalação mesmo assim? [s/N]: " continuar_nouveau
            if [[ "$continuar_nouveau" != "s" && "$continuar_nouveau" != "S" ]]; then
                echo "Instalação abortada pelo usuário."
                return 1 2>/dev/null || exit 1
            fi
        fi
    fi
}

gerar_recomendacoes() {
    echo "Analisando hardware para otimização..."
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    # Tenta rodar o recomendador apenas se o venv estiver ativo ou python3 disponível
    python3 src/smartsort/utils/recommender.py || echo "Aviso: Não foi possível gerar recomendações agora."
}


instalar_dependencias() {
    echo "Verificando dependências de sistema..."
    
    # Verifica se pacotes essenciais já existem para pular o install pesado
    if command -v tesseract &> /dev/null && command -v lspci &> /dev/null && command -v git &> /dev/null; then
        echo "Dependências de sistema já encontradas. Pulando instalação de pacotes."
        return 0
    fi

    echo "Instalando dependências de sistema para $DISTRO..."
    if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO_LIKE" == *"ubuntu"* || "$DISTRO_LIKE" == *"debian"* ]]; then
        # Só faz update se necessário
        sudo apt-get update -y
        sudo apt-get install -y python3 python3-venv python3-pip git tesseract-ocr tesseract-ocr-por pciutils mesa-utils
    elif [[ "$DISTRO" == "arch" || "$DISTRO_LIKE" == *"arch"* ]]; then
        sudo pacman -Sy --noconfirm --needed python python-pip git tesseract tesseract-data-por pciutils mesa-utils
    elif [[ "$DISTRO" == "fedora" || "$DISTRO_LIKE" == *"fedora"* ]]; then
        sudo dnf install -y python3 python3-pip git tesseract tesseract-langpack-por pciutils mesa-libGL-devel
    fi
}

configurar_python() {
    echo "Configurando ambiente Python..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    
    mkdir -p "$(pwd)/.tmp"
    export TMPDIR="$(pwd)/.tmp"

    # Usa um arquivo de controle para não reinstalar pip toda vez
    HASH_FILE=".tmp/req_hash"
    CURRENT_HASH=$(cat requirements.txt requirements-accel.txt 2>/dev/null | md5sum)
    OLD_HASH=$(cat "$HASH_FILE" 2>/dev/null)

    if [ "$CURRENT_HASH" != "$OLD_HASH" ]; then
        echo "Alteração detectada nos requisitos. Instalando dependências Python..."
        pip install --upgrade pip
        pip install -r requirements.txt
        
        if [ -f "requirements-accel.txt" ]; then
            pip install -r requirements-accel.txt || echo "Aviso: Falha em algumas dependências de aceleração."
        fi
        echo "$CURRENT_HASH" > "$HASH_FILE"
    else
        echo "Dependências Python já estão atualizadas."
    fi
}


instalar_servico() {
    echo "Instalando o serviço SmartSort no systemd..."
    if [ -f "deploy/smartsort.service" ]; then
        CURRENT_USER=$(whoami)
        PROJECT_DIR=$(pwd)
        
        sed "s|USER_PLACEHOLDER|$CURRENT_USER|g; s|WORKING_DIR_PLACEHOLDER|$PROJECT_DIR|g" deploy/smartsort.service > /tmp/smartsort.service
        
        sudo cp /tmp/smartsort.service /etc/systemd/system/smartsort.service
        sudo systemctl daemon-reload
        sudo systemctl enable smartsort.service
        sudo systemctl restart smartsort.service
        
        echo "Configurando atalho global para a CLI..."
        sudo ln -sf "$PROJECT_ROOT/smartsort-cli.sh" /usr/local/bin/smartsort
        
        echo -e "${VERDE}Serviço instalado e iniciado para o utilizador $CURRENT_USER!${NC}"
        echo -e "Agora você pode usar o comando '${AMARELO}smartsort${NC}' de qualquer lugar."
    else
        echo -e "${VERMELHO}Arquivo smartsort.service não encontrado! O serviço não pôde ser instalado.${NC}"
    fi
}


if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ "$1" != "--skip-update" ]]; then
        verificar_atualizacao
    fi
    detectar_distro
    detectar_gpu
    instalar_dependencias
    configurar_python
    gerar_recomendacoes
    instalar_servico
    echo -e "${VERDE}Instalação concluída com sucesso!${NC}"
fi
