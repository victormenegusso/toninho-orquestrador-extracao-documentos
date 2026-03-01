#!/bin/bash
# Inicia o Flower (monitoramento de workers Celery) do Toninho
set -e

cd "$(dirname "$0")/.."

exec celery -A toninho.workers.celery_app flower \
    --port=5555 \
    "$@"
