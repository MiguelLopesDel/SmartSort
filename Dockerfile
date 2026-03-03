FROM mcr.microsoft.com/devcontainers/python:3.11

# Instalar dependências do sistema para OCR (Tesseract) e suporte a Português
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
