#!/bin/bash
# Gera relatório de cobertura de testes

set -e

echo "Running tests with coverage..."

poetry run pytest \
    --cov=toninho \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml \
    --cov-fail-under=90

echo ""
echo "Coverage report generated:"
echo "  - Terminal: above"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
