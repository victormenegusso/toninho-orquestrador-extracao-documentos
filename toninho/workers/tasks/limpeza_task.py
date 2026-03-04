"""
Task de limpeza: remove logs antigos para economizar espaço.

Executada diariamente pelo Celery Beat.
"""

from datetime import UTC, datetime, timedelta

from loguru import logger

from toninho.workers.celery_app import celery_app


@celery_app.task(name="toninho.workers.tasks.limpeza_task.limpar_logs_antigos")
def limpar_logs_antigos(dias_retencao: int = 30) -> dict:
    """
    Remove logs com mais de `dias_retencao` dias.

    Args:
        dias_retencao: Número de dias para manter logs (default: 30)

    Returns:
        Dict com contagem de logs deletados
    """
    from toninho.core.database import SessionLocal
    from toninho.models.log import Log

    db = SessionLocal()

    try:
        data_limite = datetime.now(UTC) - timedelta(days=dias_retencao)

        count = (
            db.query(Log)
            .filter(Log.timestamp < data_limite)
            .delete(synchronize_session=False)
        )

        db.commit()

        logger.info(
            f"[limpeza] {count} logs deletados (retenção: {dias_retencao} dias)"
        )
        return {"logs_deletados": count, "dias_retencao": dias_retencao}

    except Exception as exc:
        db.rollback()
        logger.error(f"[limpeza] Erro ao limpar logs: {exc}")
        raise

    finally:
        db.close()
