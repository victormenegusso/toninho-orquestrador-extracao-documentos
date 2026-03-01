#!/bin/bash
# Inicia o Celery Beat (scheduler) do Toninho
set -e

cd "$(dirname "$0")/.."

exec celery -A toninho.workers.celery_app beat \
    --loglevel=info \
    "$@"
