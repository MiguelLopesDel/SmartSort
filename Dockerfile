# Estágio 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libsndfile1-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --target=/app/deps \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt


# Estágio 2: Final
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src:/app/deps
ENV PATH="/app/deps/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    pciutils \
    ffmpeg \
    libsndfile1 \
    libopenblas0 \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Copiar dependências do builder
COPY --from=builder /app/deps /app/deps

# Criar usuário não-root e pastas necessárias
RUN useradd -m smartsort && \
    mkdir -p data/sorted data/downloads_test models config && \
    chown -R smartsort:smartsort /app

# Copiar código fonte (apenas o essencial)
COPY --chown=smartsort:smartsort src/ ./src/
COPY --chown=smartsort:smartsort config/config.yaml ./config/

USER smartsort

# Healthcheck robusto (verifica se consegue carregar a config)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "from smartsort.cli.config import load_config; assert load_config() is not None" || exit 1

# Comando padrão
CMD ["python3", "-m", "smartsort"]
