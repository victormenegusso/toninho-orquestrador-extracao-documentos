#!/bin/bash
set -e

# Garantir que diretórios de volumes tenham permissão de escrita
for dir in /app/output /app/data /app/logs; do
    mkdir -p "$dir"
done

echo "Aplicando migrações do banco de dados..."
cd /app
alembic upgrade head

echo "Iniciando serviço..."
exec "$@"
