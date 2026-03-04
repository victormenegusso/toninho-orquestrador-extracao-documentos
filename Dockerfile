# Stage 1: Builder
FROM python:3.11-slim as builder

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Configurar workdir
WORKDIR /app

# Copiar arquivos de dependências
COPY pyproject.toml poetry.lock* ./

# Instalar dependências (sem dev dependencies)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd -m -u 1000 -s /bin/bash toninho

# Configurar timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Configurar workdir
WORKDIR /app

# Copiar dependências do builder
COPY --from=builder /root/.local /home/toninho/.local

# Adicionar binários ao PATH
ENV PATH=/home/toninho/.local/bin:$PATH

# Copiar código fonte
COPY --chown=toninho:toninho . .

# Tornar script executável
RUN chmod +x /app/entrypoint.sh

# Criar diretórios necessários
RUN mkdir -p /app/output /app/logs && \
    chown -R toninho:toninho /app

# Mudar para usuário não-root
USER toninho

# Expor porta da aplicação
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Usar entrypoint script e passar comando via CMD
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "toninho.main:app", "--host", "0.0.0.0", "--port", "8000"]
