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
- **GPU**: GPU dedicada obrigatória (NVIDIA, AMD Radeon RX ou Intel ARC) para aceleração de IA.
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
