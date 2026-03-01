#!/bin/bash
# Inicia um worker Celery do Toninho
set -e

cd "$(dirname "$0")/.."

exec celery -A toninho.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=100 \
    "$@"
