# 🤖 SmartSort - Organizador Inteligente de Ficheiros

O **SmartSort** é um serviço de automação local que monitoriza os seus diretórios (como a pasta de Downloads) em tempo real, classifica os novos ficheiros utilizando Inteligência Artificial e organiza-os em pastas categorizadas automaticamente.

---

## ✨ Funcionalidades

- **Monitorização em Tempo Real**: Utiliza `watchdog` para detetar novos ficheiros instantaneamente.
- **Extração de Texto Multi-Formato**: 
  - PDFs (via `pypdf`)
  - Imagens/OCR (via `pytesseract`)
  - Ficheiros de texto (`.txt`, `.csv`, `.md`)
- **Classificação Inteligente**:
  - **Zero-Shot Learning**: Classifica documentos sem treino prévio usando modelos da HuggingFace (ex: mDeBERTa).
  - **Machine Learning Local**: Modelo Scikit-Learn (Naive Bayes) treinado com os seus próprios dados.
  - **Regras de Fallback**: Organização baseada em extensões para rapidez.
- **Estrutura Profissional**: Organizado seguindo o padrão `src/` layout.

---

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.10+
- Tesseract OCR (para suporte a imagens)
  ```bash
  # Ubuntu/Debian
  sudo apt install tesseract-ocr tesseract-ocr-por
  ```

### Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/MiguelLopesDel/SmartSort.git
   cd SmartSort
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuração

Edite o ficheiro `config/config.yaml` para definir as suas preferências:

```yaml
directories_to_watch:
  - "data/downloads_test"
destination_base_folder: "data/sorted"

ai_classification:
  enabled: true
  mode: "zero_shot" # Opções: zero_shot, local_ml, api
  categorias_disponiveis: ["Financas", "Trabalho", "Pessoal", "Saude"]
```

---

## 🛠️ Como Usar

### Iniciar o Monitorizador
Para começar a organizar os seus ficheiros automaticamente:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 -m smartsort
```

### Treinar o Modelo de ML Local (Opcional)
Se preferir usar o modo `local_ml`, treine o modelo com os seus dados:
```bash
python3 -c "from smartsort.core.trainer import treinar; treinar()"
```

---

## 📂 Estrutura do Projeto

```text
SmartSort/
├── config/          # Configurações (.yaml)
├── data/            # Pastas de teste e destino
├── deploy/          # Docker e Scripts de Serviço
├── models/          # Modelos de ML guardados
├── src/
│   └── smartsort/   # Código fonte principal
│       ├── core/    # Engine e Lógica de IA
│       └── utils/   # Helpers (OCR, PDF)
└── tests/           # Suite de testes
```

---

## 📄 Licença
Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---
*Desenvolvido por [Miguel Lopes](https://github.com/MiguelLopesDel)*
