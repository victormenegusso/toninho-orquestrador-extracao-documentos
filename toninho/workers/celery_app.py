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
    include=[
        "toninho.workers.tasks.execucao_task",
        "toninho.workers.tasks.agendamento_task",
        "toninho.workers.tasks.limpeza_task",
    ],
)

# Configurações do Celery
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Tracking
    task_track_started=True,
    # Limites de tempo
    task_time_limit=7200,  # 2 horas (hard limit — SIGKILL)
    task_soft_time_limit=7000,  # 1h56min (soft — SoftTimeLimitExceeded)
    # Confiabilidade: ACK só após concluir (evita perda de task se worker cair)
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Concorrência
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_concurrency=settings.WORKER_CONCURRENCY,
    # Beat schedule (tarefas periódicas)
    beat_schedule={
        "verificar-agendamentos": {
            "task": "toninho.workers.tasks.agendamento_task.verificar_agendamentos",
            "schedule": 60.0,  # A cada 60 segundos
        },
        "limpar-logs-antigos": {
            "task": "toninho.workers.tasks.limpeza_task.limpar_logs_antigos",
            "schedule": 86400.0,  # Diariamente
        },
    },
)
