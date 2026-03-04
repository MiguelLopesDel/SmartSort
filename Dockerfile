FROM python:3.11-slim

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Instalar dependências do sistema para OCR (Tesseract) e utilitários
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    pciutils \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o código fonte e arquivos necessários
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY models/ ./models/

# Comando padrão
CMD ["python3", "-m", "smartsort"]
