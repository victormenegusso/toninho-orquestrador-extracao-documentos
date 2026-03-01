"""
Configuração do Celery para processamento assíncrono.

Este módulo configura a aplicação Celery com Redis como broker
e backend de resultados.
"""

from celery import Celery

from toninho.core.config import settings

# Criar aplicação Celery
celery_app = Celery(
    "toninho",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora
    task_soft_time_limit=3300,  # 55 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["toninho.workers"])
