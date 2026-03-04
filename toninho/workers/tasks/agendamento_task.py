"""
Task de agendamento: verifica configurações com cron e cria execuções.

Executada periodicamente pelo Celery Beat (a cada 60 segundos).
"""

from datetime import datetime, timedelta, timezone

from croniter import croniter
from loguru import logger

from toninho.workers.celery_app import celery_app


@celery_app.task(name="toninho.workers.tasks.agendamento_task.verificar_agendamentos")
def verificar_agendamentos() -> dict:
    """
    Verifica configurações com agendamento RECORRENTE e cria execuções
    se necessário.

    Para cada configuração com agendamento_cron definido:
    1. Calcula a próxima execução esperada via croniter
    2. Se dentro da janela de 60 segundos, verifica se já há execução recente
    3. Se não houver, cria nova execução e enfileira a task

    Returns:
        Dict com quantidade de execuções criadas
    """
    from toninho.core.database import SessionLocal
    from toninho.models.configuracao import Configuracao
    from toninho.models.execucao import Execucao
    from toninho.models.enums import AgendamentoTipo, ExecucaoStatus
    from toninho.workers.tasks.execucao_task import executar_processo_task

    db = SessionLocal()
    agendadas = 0

    try:
        # Buscar configurações com agendamento RECORRENTE
        configuracoes = (
            db.query(Configuracao)
            .filter(
                Configuracao.agendamento_tipo == AgendamentoTipo.RECORRENTE,
                Configuracao.agendamento_cron.isnot(None),
            )
            .all()
        )

        agora = datetime.now(timezone.utc)
        janela = timedelta(seconds=60)

        for config in configuracoes:
            try:
                cron = croniter(config.agendamento_cron, agora - timedelta(minutes=2))
                proxima = cron.get_next(datetime)

                # Executar se dentro dos próximos 60 segundos
                if proxima <= agora + janela:
                    # Evitar duplicatas: verificar execuções recentes (últimos 5 min)
                    ultima = (
                        db.query(Execucao)
                        .filter(
                            Execucao.processo_id == config.processo_id,
                            Execucao.created_at >= agora - timedelta(minutes=5),
                        )
                        .first()
                    )

                    if ultima is None:
                        execucao = Execucao(
                            processo_id=config.processo_id,
                            status=ExecucaoStatus.AGUARDANDO,
                        )
                        db.add(execucao)
                        db.commit()
                        db.refresh(execucao)

                        # Enfileirar task
                        executar_processo_task.delay(str(execucao.id))
                        agendadas += 1
                        logger.info(
                            f"[agendamento] Execução criada: execucao_id={execucao.id} "
                            f"processo_id={config.processo_id}"
                        )

            except Exception as exc:
                logger.error(
                    f"[agendamento] Erro ao processar configuracao_id={config.id}: {exc}"
                )

    finally:
        db.close()

    logger.info(f"[agendamento] {agendadas} execuções agendadas")
    return {"execucoes_criadas": agendadas}
