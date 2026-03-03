# Imagem de produção para SmartSort
FROM python:3.11-slim

# Instalar dependências do sistema para OCR (Tesseract) e Português
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar requisitos e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código fonte
COPY . .

# Comando padrão para rodar o serviço
CMD ["python3", "-m", "src.smartsort"]