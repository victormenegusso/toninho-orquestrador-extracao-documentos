"""
Task principal de execução de processos de extração.

A task `executar_processo_task` é chamada via Celery e orquestra
toda a extração de URLs para uma dada execução.
"""

import uuid
from typing import Any, Dict

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from loguru import logger

from toninho.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="toninho.workers.executar_processo",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    # Não auto-retry em erros de negócio (ValueError)
    dont_autoretry_for=(ValueError,),
)
def executar_processo_task(self: Task, execucao_id: str) -> Dict[str, Any]:
    """
    Task Celery para executar um processo de extração.

    Fluxo:
        1. Busca execução no banco
        2. Atualiza status → EM_EXECUCAO
        3. Busca configuração do processo
        4. Para cada URL: extrai, salva e registra PaginaExtraida + Log
        5. Atualiza métricas e status final

    Args:
        execucao_id: UUID da execução (string)

    Returns:
        Dict com status, paginas_sucesso, paginas_falha, total, bytes_extraidos
    """
    from toninho.core.database import SessionLocal
    from toninho.workers.utils import ExtractionOrchestrator

    logger.info(f"[task] Iniciando execucao_id={execucao_id}")

    db = SessionLocal()
    try:
        orchestrator = ExtractionOrchestrator(db)
        resultado = orchestrator.run(uuid.UUID(execucao_id))

        logger.info(
            f"[task] Execucao {execucao_id} concluída: "
            f"status={resultado['status'].value}, "
            f"sucesso={resultado['paginas_sucesso']}, "
            f"falha={resultado['paginas_falha']}"
        )
        return {
            "status": resultado["status"].value,
            "paginas_sucesso": resultado["paginas_sucesso"],
            "paginas_falha": resultado["paginas_falha"],
            "total": resultado["total"],
            "bytes_extraidos": resultado["bytes_extraidos"],
        }

    except SoftTimeLimitExceeded:
        logger.error(f"[task] SoftTimeLimitExceeded para execucao_id={execucao_id}")
        _marcar_falha(db, execucao_id, "Timeout de execução atingido")
        raise

    except ValueError as exc:
        # Erros de negócio (sem retry)
        logger.error(f"[task] Erro de negócio para execucao_id={execucao_id}: {exc}")
        _marcar_falha(db, execucao_id, str(exc))
        raise

    except Exception as exc:
        logger.error(f"[task] Erro inesperado para execucao_id={execucao_id}: {exc}")
        # Retry automático configurado via autoretry_for
        raise

    finally:
        db.close()


def _marcar_falha(db, execucao_id: str, motivo: str) -> None:
    """Marca execução como FALHOU e registra log."""
    try:
        import uuid as _uuid
        from datetime import datetime, timezone
        from toninho.models.execucao import Execucao
        from toninho.models.enums import ExecucaoStatus, LogNivel
        from toninho.workers.utils import ExtractionOrchestrator

        eid = _uuid.UUID(execucao_id)
        execucao = db.get(Execucao, eid)
        if execucao:
            execucao.status = ExecucaoStatus.FALHOU
            execucao.finalizado_em = datetime.now(timezone.utc)
            db.commit()

        ExtractionOrchestrator._add_log(db, eid, LogNivel.ERROR, f"Task falhou: {motivo}")
        db.commit()
    except Exception as inner:
        logger.error(f"Erro ao marcar falha: {inner}")
