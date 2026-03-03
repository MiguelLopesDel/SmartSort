---

# 🤖 SmartSort

O **SmartSort** é um organizador inteligente de arquivos que funciona como um serviço em segundo plano no seu computador. Ele monitora a sua pasta de Downloads (ou qualquer outra pasta que você escolher) e organiza magicamente seus arquivos, PDFs, imagens e textos para as pastas corretas de projeto ou categoria.

A verdadeira magia do **SmartSort** está no fato de ele não olhar apenas para o nome do arquivo, mas sim para o **significado do seu conteúdo**.

## 🌟 Funcionalidades

1. **Monitoramento Invisível:** Fica silenciosamente à espreita. Assim que você termina um download, ele entra em ação.
2. **Leitura de Texto (OCR e PDF):** Lê o conteúdo de arquivos PDF nativos e também de **imagens** (fotos de recibos, notas fiscais) usando tecnologia OCR.
3. **Privacidade Total (IA Local Zero-Shot):** O sistema não depende de palavras-chave rígidas ("se tiver 'nota' vai para 'finanças'"). Ele utiliza um modelo avançado de IA de Processamento de Linguagem Natural (HuggingFace Zero-Shot) que roda 100% offline no seu PC para "entender" o texto e prever a categoria correta.

---

## 🚀 Como Instalar e Iniciar

### 1. Pré-requisitos (Ubuntu/Debian)

O software precisa que você tenha instalado o Python, o Tesseract (para ler imagens) e as bibliotecas base:

```bash
sudo apt-get update
sudo apt-get install python3-venv tesseract-ocr tesseract-ocr-por

```

### 2. Configurar o Ambiente

Na pasta raiz do projeto, instale as dependências virtuais (pode demorar alguns minutos na primeira vez devido ao PyTorch):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

### 3. Primeira Execução

Recomendamos executar o programa manualmente na primeira vez. O motor de IA avançado (HuggingFace) vai baixar um pacote neural de aproximadamente 500MB uma única vez para o seu computador.

```bash
PYTHONPATH=src ./venv/bin/python src/main.py

```

Se tudo der certo, você pode pressionar `Ctrl+C` para parar.

### 4. Transformar em um Serviço Permanente (Opcional, Linux)

Se quiser que o seu Linux inicie o SmartSort assim que você ligar o PC e que ele rode em background para sempre, criamos um instalador! Basta executar:

```bash
chmod +x install.sh
./install.sh

```

---

## ⚙️ Configuração (O Arquivo `config.yaml`)

Todo o comportamento do seu robô pode ser alterado abrindo o arquivo `config.yaml`.

```yaml
directories_to_watch:
    - "/caminho/para/seus/Downloads"
destination_base_folder: "/caminho/para/seus/Documentos/Organizados"

ai_classification:
    enabled: true
    mode: "zero_shot"
    categorias_disponiveis: ["Financas", "Trabalho", "Pessoal", "Saude", "Educacao", "Projetos"]
```

**Como Ensinar Novas Categorias?**
Você não precisa ensinar! Na linha `categorias_disponiveis` do `config.yaml`, basta digitar as palavras que deseja. A Inteligência Artificial vai ler seus novos documentos e associá-los de forma semântica e inteligente às novas categorias que você inventou.

---

## 🧪 Como Rodar os Testes

Se você editar o código e quiser garantir que não quebrou nada, rode os testes (unitários e de integração):

```bash
PYTHONPATH=src ./venv/bin/pytest tests/ -v

```
