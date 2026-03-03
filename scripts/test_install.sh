#!/bin/bash

cd "$(dirname "$0")/.."


VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
NC='\033[0m'

echo "Iniciando testes do script install.sh..."


export MOCK_OS_RELEASE="/tmp/os-release-mock"
export MOCK_LSPCI_OUTPUT=""
export MOCK_LSMOD_OUTPUT=""
export MOCK_MODINFO_OUTPUT=""
export MOCK_COMMAND_V=""


command() {
    if [[ "$1" == "-v" ]]; then
        if [[ "$MOCK_COMMAND_V" == "false" ]]; then
            return 1
        fi
        return 0
    fi
    builtin command "$@"
}

lspci() {
    echo "$MOCK_LSPCI_OUTPUT"
}

lsmod() {
    echo "$MOCK_LSMOD_OUTPUT"
}

modinfo() {
    echo "$MOCK_MODINFO_OUTPUT"
}


source scripts/install.sh

test_distro_ubuntu() {
    echo -n "Testando detecção de Ubuntu... "
    cat << EOF > "$MOCK_OS_RELEASE"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 22.04 LTS"
EOF
    
    OUTPUT=$(detectar_distro)
    if echo "$OUTPUT" | grep -q "Ubuntu"; then
        echo -e "${VERDE}Passou${NC}"
    else
        echo -e "${VERMELHO}Falhou${NC}"
        echo "$OUTPUT"
    fi
}

test_distro_arch() {
    echo -n "Testando detecção de Arch Linux... "
    cat << EOF > "$MOCK_OS_RELEASE"
ID=arch
PRETTY_NAME="Arch Linux"
EOF
    
    OUTPUT=$(detectar_distro)
    if echo "$OUTPUT" | grep -q "Arch Linux"; then
        echo -e "${VERDE}Passou${NC}"
    else
        echo -e "${VERMELHO}Falhou${NC}"
        echo "$OUTPUT"
    fi
}

test_gpu_nvidia_proprietario() {
    echo -n "Testando GPU NVIDIA com Driver Proprietário... "
    export MOCK_COMMAND_V="true"
    export MOCK_LSPCI_OUTPUT="01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3070] [10de:2484] (rev a1)"
    export MOCK_LSMOD_OUTPUT="nvidia_drm 1234 0
nvidia_modeset 1234 1 nvidia_drm
nvidia 1234 1234"
    export MOCK_MODINFO_OUTPUT="license: NVIDIA"
    
    OUTPUT=$(detectar_gpu)
    
    if echo "$OUTPUT" | grep -q "NVIDIA Proprietário"; then
         echo -e "${VERDE}Passou${NC}"
    else
         echo -e "${VERMELHO}Falhou${NC}"
         echo "$OUTPUT"
    fi
}

test_gpu_nvidia_nouveau() {
    echo -n "Testando GPU NVIDIA com Driver Nouveau... "
    export MOCK_LSPCI_OUTPUT="01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3070] [10de:2484] (rev a1)"
    export MOCK_LSMOD_OUTPUT="nouveau 1234 0"
    

    OUTPUT=$(echo "s" | detectar_gpu)
    
    if echo "$OUTPUT" | grep -q "Nouveau"; then
         echo -e "${VERDE}Passou${NC}"
    else
         echo -e "${VERMELHO}Falhou${NC}"
         echo "$OUTPUT"
    fi
}

test_gpu_amd() {
    echo -n "Testando GPU AMD Dedicada (Radeon RX)... "
    export MOCK_LSPCI_OUTPUT="03:00.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. [AMD/ATI] Navi 21 [Radeon RX 6800/6800 XT / 6900 XT] (rev c1)"
    
    OUTPUT=$(detectar_gpu)
    
    if echo "$OUTPUT" | grep -q "AMD Dedicada"; then
         echo -e "${VERDE}Passou${NC}"
    else
         echo -e "${VERMELHO}Falhou${NC}"
         echo "$OUTPUT"
    fi
}

test_gpu_intel_arc() {
    echo -n "Testando GPU Intel Dedicada (ARC)... "
    export MOCK_LSPCI_OUTPUT="03:00.0 VGA compatible controller [0300]: Intel Corporation DG2 [Arc A770] [8086:56a0] (rev 08)"
    
    OUTPUT=$(detectar_gpu)
    
    if echo "$OUTPUT" | grep -q "Intel Dedicada (ARC)"; then
         echo -e "${VERDE}Passou${NC}"
    else
         echo -e "${VERMELHO}Falhou${NC}"
         echo "$OUTPUT"
    fi
}

test_gpu_integrada() {
    echo -n "Testando abortar com GPU Integrada... "
    export MOCK_LSPCI_OUTPUT="00:02.0 VGA compatible controller [0300]: Intel Corporation CometLake-H GT2 [UHD Graphics] [8086:9bc4] (rev 05)"
    

    OUTPUT=$(detectar_gpu 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -ne 0 ] && echo "$OUTPUT" | grep -q "Vou resolver isso depois"; then
         echo -e "${VERDE}Passou${NC}"
    else
         echo -e "${VERMELHO}Falhou${NC}"
         echo "Código de saída: $EXIT_CODE"
         echo "Saída:"
         echo "$OUTPUT"
    fi
}

test_sem_gpu() {
    echo -n "Testando abortar sem GPU... "
    export MOCK_LSPCI_OUTPUT=""
    
    OUTPUT=$(detectar_gpu 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -ne 0 ] && echo "$OUTPUT" | grep -q "Vou resolver isso depois"; then
         echo -e "${VERDE}Passou${NC}"
    else
         echo -e "${VERMELHO}Falhou${NC}"
         echo "Código de saída: $EXIT_CODE"
    fi
}

test_distro_ubuntu
test_distro_arch
test_gpu_nvidia_proprietario
test_gpu_nvidia_nouveau
test_gpu_amd
test_gpu_intel_arc
test_gpu_integrada
test_sem_gpu

rm -f "$MOCK_OS_RELEASE"
echo "Testes concluídos!"
