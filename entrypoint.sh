#!/bin/bash
set -e

echo "Aplicando migrações do banco de dados..."
cd /app
alembic upgrade head

echo "Iniciando serviço..."
exec "$@"
