"""
Configurações específicas dos workers Celery.
"""

from toninho.core.config import settings


class WorkerConfig:
    """Configurações dos workers."""

    # Concurrency
    concurrency: int = settings.WORKER_CONCURRENCY
    max_concurrent_processes: int = settings.MAX_CONCURRENT_PROCESSES

    # Task lifecycle
    task_time_limit: int = 7200  # 2 horas (hard limit)
    task_soft_time_limit: int = 7000  # ~1h56min (soft limit — aviso antes de kill)
    max_tasks_per_child: int = 100  # Recicla worker após 100 tasks
    prefetch_multiplier: int = 1  # Pega 1 task por vez

    # Retry
    max_retries: int = settings.MAX_RETRIES
    default_retry_delay: int = 60  # segundos
    retry_backoff: bool = True
    retry_jitter: bool = True

    # Limpeza
    log_retention_days: int = 30

    # Agendamento Beat
    scheduling_interval_seconds: float = 60.0  # verificar_agendamentos
    cleanup_interval_seconds: float = 86400.0  # limpar_logs_antigos


worker_config = WorkerConfig()
