"""
Módulo de workers Celery para processamento assíncrono.

Exporta a aplicação Celery e o orquestrador de extração.
"""

from toninho.workers.celery_app import celery_app
from toninho.workers.utils import ExtractionOrchestrator

__all__ = ["celery_app", "ExtractionOrchestrator"]
