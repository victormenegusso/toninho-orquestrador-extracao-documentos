#!/bin/bash

# Script para executar testes

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Executando Testes${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${YELLOW}Executando pytest com coverage...${NC}"
poetry run pytest -v --cov=toninho --cov-report=html --cov-report=term-missing

echo ""
echo -e "${GREEN}✓ Testes concluídos!${NC}"
echo ""
echo -e "Relatório HTML gerado em: ${YELLOW}htmlcov/index.html${NC}"
echo -e "Abra com: ${YELLOW}open htmlcov/index.html${NC}"
echo ""
