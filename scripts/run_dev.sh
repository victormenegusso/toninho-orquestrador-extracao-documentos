#!/bin/bash

# Script para executar ambiente de desenvolvimento com Docker

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Iniciando Ambiente de Desenvolvimento${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo -e "${RED}✗ Arquivo .env não encontrado!${NC}"
    echo -e "Execute primeiro: ${YELLOW}./scripts/setup.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}Levantando serviços Docker...${NC}"
echo ""

# Levantar serviços com rebuild
docker-compose up --build

# Note: O comando acima bloqueia e mostra os logs
# Para rodar em background, use: docker-compose up --build -d
