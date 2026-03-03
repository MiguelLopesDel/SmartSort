#!/bin/bash

cd "$(dirname "$0")/.."

VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
NC='\033[0m'

echo -e "${VERDE}Bem-vindo ao instalador do SmartSort!${NC}"


verificar_atualizacao() {
    echo "Verificando se há atualizações no repositório..."
    if command -v git &> /dev/null && [ -d ".git" ]; then
        git fetch > /dev/null 2>&1
        LOCAL=$(git rev-parse @ 2>/dev/null)
        REMOTE=$(git rev-parse @{u} 2>/dev/null)
        
        if [ "$LOCAL" != "$REMOTE" ] && [ -n "$REMOTE" ]; then
            echo -e "${AMARELO}Uma atualização foi encontrada no repositório.${NC}"
            read -p "Deseja baixar a atualização agora? [s/N]: " atualizar
            if [[ "$atualizar" == "s" || "$atualizar" == "S" ]]; then
                git pull
                echo -e "${VERDE}Atualização concluída. Reiniciando o instalador com a versão mais recente...${NC}"
                exec "$0" "--skip-update"
            fi
        else
            echo "O repositório já está atualizado."
        fi
    else
         echo "Este diretório não é um repositório git ou o git não está instalado. Pulando a verificação de atualizações."
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
        echo -e "${VERMELHO}Nenhuma GPU dedicada suportada (AMD RX, NVIDIA, Intel ARC) foi detectada.${NC}"
        echo -e "${AMARELO}Encontrado no sistema: ${GPU_INFO}${NC}"
        echo -e "${VERMELHO}Por enquanto o programa não é suportado para rodar apenas em CPU ou GPU integrada. Vou resolver isso depois.${NC}"
        return 1 2>/dev/null || exit 1
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


instalar_dependencias() {
    echo "Instalando dependências de sistema para $DISTRO..."
    
    if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO_LIKE" == *"ubuntu"* || "$DISTRO_LIKE" == *"debian"* ]]; then
        echo "Executando apt-get..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip git tesseract-ocr tesseract-ocr-por pciutils mesa-utils
    elif [[ "$DISTRO" == "arch" || "$DISTRO_LIKE" == *"arch"* ]]; then
        echo "Executando pacman..."
        sudo pacman -Sy --noconfirm --needed python python-pip git tesseract tesseract-data-por pciutils mesa-utils
    elif [[ "$DISTRO" == "fedora" || "$DISTRO_LIKE" == *"fedora"* ]]; then
        echo "Executando dnf..."
        sudo dnf install -y python3 python3-pip git tesseract tesseract-langpack-por pciutils mesa-libGL-devel
    else
        echo -e "${VERMELHO}Distribuição não suportada automaticamente para instalação de pacotes.${NC}"
        echo "Por favor, certifique-se de que os pacotes básicos estão instalados: python3, git, tesseract-ocr, pciutils"
    fi
}


configurar_python() {
    echo "Configurando ambiente virtual Python..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    
    echo "Instalando requisitos do Python..."
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
         echo -e "${AMARELO}Arquivo requirements.txt não encontrado! Pulando instalação de pacotes Python.${NC}"
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
        echo -e "${VERDE}Serviço instalado e iniciado para o utilizador $CURRENT_USER!${NC}"
        echo "Use 'sudo systemctl status smartsort' para ver o status."
    else
        echo -e "${VERMELHO}Arquivo smartsort.service não encontrado! O serviço não pôde ser instalado.${NC}"
    fi
}


if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ "$1" != "--skip-update" ]]; then
        verificar_atualizacao
    fi
    detectar_distro
    detectar_gpu || exit 1
    instalar_dependencias
    configurar_python
    instalar_servico
    echo -e "${VERDE}Instalação concluída com sucesso!${NC}"
fi
