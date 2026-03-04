"""
Módulo de health checks do Toninho.

Verifica saúde de database, Redis e Celery workers.
"""

import time
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthCheckService:
    """Serviço de health checks."""

    def __init__(
        self,
        db: Session,
        celery_app=None,
        redis_client=None,
    ):
        self.db = db
        self.celery_app = celery_app
        self.redis_client = redis_client

    def check_all(self) -> dict[str, Any]:
        """
        Executa todos os health checks disponíveis.

        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "timestamp": ISO timestamp,
                "checks": {
                    "database": {...},
                    "redis": {...},       # Apenas se redis_client configurado
                    "celery_workers": {...}  # Apenas se celery_app configurado
                }
            }
        """
        checks: dict[str, Any] = {}

        # Database check (sempre executado)
        checks["database"] = self._check_database()

        # Redis check (opcional)
        if self.redis_client is not None:
            checks["redis"] = self._check_redis()

        # Celery workers check (opcional)
        if self.celery_app is not None:
            checks["celery_workers"] = self._check_celery_workers()

        # Overall status
        all_healthy = all(c["status"] == "healthy" for c in checks.values())
        any_unhealthy = any(c["status"] == "unhealthy" for c in checks.values())

        if all_healthy:
            overall_status = "healthy"
        elif any_unhealthy:
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": checks,
        }

    def _check_database(self) -> dict[str, Any]:
        """Verifica conexão com database."""
        try:
            start = time.time()
            self.db.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000  # ms

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_redis(self) -> dict[str, Any]:
        """Verifica conexão com Redis."""
        try:
            start = time.time()
            self.redis_client.ping()
            latency = (time.time() - start) * 1000  # ms

            info = self.redis_client.info()

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_celery_workers(self) -> dict[str, Any]:
        """Verifica workers Celery."""
        try:
            inspect = self.celery_app.control.inspect(timeout=2.0)
            stats = inspect.stats()
            active = inspect.active()

            if not stats:
                return {
                    "status": "degraded",
                    "error": "No workers available",
                    "worker_count": 0,
                    "active_tasks": 0,
                }

            worker_count = len(stats)
            active_tasks = sum(len(tasks) for tasks in active.values()) if active else 0

            return {
                "status": "healthy",
                "worker_count": worker_count,
                "active_tasks": active_tasks,
                "workers": list(stats.keys()),
            }

        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                "status": "degraded",
                "error": str(e),
                "worker_count": 0,
                "active_tasks": 0,
            }
