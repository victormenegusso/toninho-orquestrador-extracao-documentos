#!/bin/bash

# Script para abrir shell no container da API

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Abrindo shell no container toninho-api...${NC}"
echo ""

# Verificar se container está rodando
if [ ! "$(docker ps -q -f name=toninho-api)" ]; then
    echo -e "${RED}✗ Container toninho-api não está rodando!${NC}"
    echo -e "Execute primeiro: ${YELLOW}./scripts/run_dev.sh${NC}"
    exit 1
fi

# Abrir shell
docker-compose exec api bash
