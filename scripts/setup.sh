#!/bin/bash

# Setup inicial do projeto Toninho
# Este script configura o ambiente de desenvolvimento completo

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Setup do Projeto Toninho${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verificar pré-requisitos
echo -e "${YELLOW}Verificando pré-requisitos...${NC}"

# Verificar Poetry
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}✗ Poetry não encontrado!${NC}"
    echo -e "Instale com: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi
echo -e "${GREEN}✓ Poetry instalado${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker não encontrado!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker instalado${NC}"

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose não encontrado!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose instalado${NC}"

echo ""

# Copiar .env.example para .env se não existir
if [ ! -f .env ]; then
    echo -e "${YELLOW}Criando arquivo .env...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Arquivo .env criado${NC}"
    echo -e "${YELLOW}⚠ Por favor, revise e ajuste as variáveis em .env${NC}"
else
    echo -e "${GREEN}✓ Arquivo .env já existe${NC}"
fi

echo ""

# Instalar dependências Poetry
echo -e "${YELLOW}Instalando dependências Python...${NC}"
poetry install
echo -e "${GREEN}✓ Dependências instaladas${NC}"

echo ""

# Instalar pre-commit hooks
echo -e "${YELLOW}Instalando pre-commit hooks...${NC}"
poetry run pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks instalados${NC}"

echo ""

# Criar diretório output se não existir
if [ ! -d "output" ]; then
    mkdir -p output
    echo -e "${GREEN}✓ Diretório output criado${NC}"
else
    echo -e "${GREEN}✓ Diretório output já existe${NC}"
fi

echo ""

# Build imagens Docker (opcional, comentado por padrão)
# echo -e "${YELLOW}Construindo imagens Docker...${NC}"
# docker-compose build
# echo -e "${GREEN}✓ Imagens Docker construídas${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Setup Concluído!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Próximos passos:"
echo -e "  1. Revise o arquivo .env e ajuste as configurações"
echo -e "  2. Execute: ${YELLOW}./scripts/run_dev.sh${NC} para iniciar o ambiente"
echo -e "  3. Ou execute: ${YELLOW}make run${NC} para rodar localmente"
echo -e ""
echo -e "Comandos úteis:"
echo -e "  ${YELLOW}make help${NC}            - Ver todos os comandos disponíveis"
echo -e "  ${YELLOW}make test${NC}            - Executar testes"
echo -e "  ${YELLOW}make format${NC}          - Formatar código"
echo -e "  ${YELLOW}./scripts/shell.sh${NC}   - Abrir shell no container"
echo ""
