# Escolha uma imagem base oficial da Microsoft (existem para Python, Go, Rust, etc.)
FROM mcr.microsoft.com/devcontainers/javascript-node:20

# Instalar pacotes adicionais do SO para facilitar o debug e uso do terminal
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends vim curl procps

# Instalar o pnpm globalmente, que é muito mais rápido que o npm padrão
RUN su node -c "npm install -g pnpm"

# Configurar o diretório de trabalho padrão
WORKDIR /workspaces/${localWorkspaceFolderBasename}
