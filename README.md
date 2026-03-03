# 🤖 SmartSort - Organizador Inteligente de Ficheiros

O **SmartSort** é um serviço de automação para Linux que monitoriza diretórios em tempo real, classifica ficheiros utilizando Inteligência Artificial (local ou remota) e organiza-os automaticamente.

---

## ✨ Funcionalidades

- **Monitorização em Tempo Real**: Deteção instantânea via `watchdog`.
- **Extração de Texto Multi-Formato**: Suporte para PDFs, Imagens (OCR via Tesseract) e ficheiros de texto.
- **Classificação por IA**:
  - **Zero-Shot Learning**: Modelos HuggingFace (ex: mDeBERTa) para classificação sem treino.
  - **Machine Learning Local**: Scikit-Learn (Naive Bayes) customizável.
- **Aceleração por Hardware**: Suporte total para **GPUs Integradas (Intel/AMD)** via **OpenVINO** e **ONNX Runtime**, com quantização INT8.
- **Otimização para Notebooks**: Modo **Battery Saver** que pausa tarefas pesadas e reduz frequência de varredura ao desligar da tomada.
- **Daemonização**: Integração total com `systemd` para execução em segundo plano.

---

## 💻 Interface de Linha de Comando (CLI)

O SmartSort inclui uma ferramenta de configuração visual para facilitar a gestão do serviço.

### Comandos Disponíveis

| Comando | Descrição | Exemplo de Uso |
| :--- | :--- | :--- |
| `show` | Visualiza todas as configurações atuais em formato de tabela. | `smartsort show` |
| `status` | Exibe o status do hardware em tempo real (CPU, RAM, Bateria). | `smartsort status` |
| `accel` | Configura o motor de aceleração (CUDA, OpenVINO ou CPU). | `smartsort accel cuda gpu` |
| `model` | Troca o modelo de Inteligência Artificial utilizado. | `smartsort model nome-do-modelo` |
| `add-dir` | Adiciona um novo diretório à lista de monitorização. | `smartsort add-dir ~/Downloads` |
| `rm-dir` | Remove um diretório da monitorização. | `smartsort rm-dir ~/Downloads` |
| `battery-mode` | Ativa ou desativa o modo de poupança de energia. | `smartsort battery-mode --on` |

> **Nota:** O comando global `smartsort` é configurado automaticamente durante a instalação.

---

## 🚀 Instalação Automatizada (Recomendado)

O SmartSort inclui um script de instalação inteligente que deteta a sua distribuição (Ubuntu, Debian, Arch, Fedora), verifica o hardware de GPU e configura o ambiente Python e o serviço de sistema.

```bash
git clone https://github.com/MiguelLopesDel/SmartSort.git
cd SmartSort
chmod +x scripts/install.sh
./scripts/install.sh
```

### O que o instalador faz:
1. **Verifica Atualizações**: Garante que tem a versão mais recente do código.
2. **Hardware Check**: Valida se possui uma GPU dedicada suportada.
3. **Dependências do Sistema**: Instala `tesseract-ocr`, `python3-venv`, `pciutils`, etc.
4. **Ambiente Python**: Cria o `venv` e instala os `requirements.txt`.
5. **Systemd**: Instala e inicia o serviço `smartsort.service`.

---

## 💻 Requisitos de Sistema

- **SO**: Linux (Distribuições baseadas em Debian, Arch ou Fedora).
- **Init System**: **systemd** (Obrigatório para o modo Daemon/Serviço).
- **Hardware**: 
  - **GPU Dedicada**: NVIDIA (CUDA), AMD (OpenVINO/CPU) ou Intel ARC.
  - **GPU Integrada**: Intel Iris Xe, AMD Radeon Graphics (via OpenVINO).
  - **CPU**: Mínimo de 4GB de RAM e suporte a instruções AVX2.
- **OCR**: Tesseract OCR (instalado automaticamente pelo script).

---

## ⚙️ Configuração

As definições estão centralizadas em `config/config.yaml`:

```yaml
directories_to_watch:
  - "data/downloads_test"
destination_base_folder: "data/sorted"

ai_classification:
  enabled: true
  mode: "zero_shot" # Opções: zero_shot, local_ml, api
  categorias_disponiveis: ["Financas", "Trabalho", "Pessoal", "Saude"]
```

### 🧹 Reorganização de Ficheiros Existentes
Por padrão, o SmartSort **reorganiza automaticamente** todos os ficheiros que já se encontram nas pastas vigiadas assim que o serviço arranca. 

Esta funcionalidade garante que o seu diretório seja limpo imediatamente, sem precisar de esperar por novos eventos de download. A lógica de segurança impede que ficheiros ocultos (como `.gitkeep`) ou subpastas sejam movidos indevidamente.

---

## 🛠️ Gestão do Serviço

Após a instalação, pode gerir o SmartSort como qualquer outro serviço Linux:

```bash
# Verificar status
sudo systemctl status smartsort

# Reiniciar após mudar configurações
sudo systemctl restart smartsort

# Ver logs em tempo real
journalctl -u smartsort -f
```

---

## 📂 Estrutura do Projeto

```text
SmartSort/
├── config/          # Configuração do utilizador
├── data/            # Pastas de processamento e destino
├── deploy/          # Ficheiro de serviço systemd e Docker
├── scripts/         # Instalador e utilitários de manutenção
├── src/smartsort/   # Código fonte (Pacote Python)
└── tests/           # Testes unitários
```

---
*Desenvolvido por [Miguel Lopes](https://github.com/MiguelLopesDel)*
