#!/bin/bash

# Script para executar migrations do Alembic

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Executando Migrations${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verificar se está usando Docker ou local
if [ "$(docker ps -q -f name=toninho-api)" ]; then
    echo -e "${YELLOW}Executando migrations no container...${NC}"
    docker-compose exec api poetry run alembic upgrade head
else
    echo -e "${YELLOW}Executando migrations localmente...${NC}"
    poetry run alembic upgrade head
fi

echo ""
echo -e "${GREEN}✓ Migrations executadas com sucesso!${NC}"
echo ""
