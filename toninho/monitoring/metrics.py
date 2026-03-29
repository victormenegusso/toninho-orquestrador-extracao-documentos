"""
Módulo de métricas do Toninho.

Calcula métricas operacionais e do dashboard.
"""

from typing import Any

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from toninho.models.configuracao import Configuracao
from toninho.models.enums import AgendamentoTipo, ExecucaoStatus
from toninho.models.execucao import Execucao
from toninho.models.processo import Processo


class MetricsService:
    """Serviço de cálculo de métricas."""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_metrics(self) -> dict[str, Any]:
        """
        Métricas para o dashboard.

        Returns:
            {
                "executions": {
                    "total": int,
                    "active": int,
                    "completed": int,
                    "failed": int,
                    "pending": int
                },
                "processes": {
                    "total": int,
                    "with_schedule": int
                },
                "success_rate": float,
                "avg_duration_minutes": float,
                "recent_activity": [...]
            }
        """
        try:
            return {
                "executions": self._count_executions_by_status(),
                "processes": self._count_processes(),
                "success_rate": self._calculate_success_rate(),
                "avg_duration_minutes": self._calculate_avg_duration(),
                "recent_activity": self._get_recent_activity(),
            }
        except Exception as e:
            logger.error(f"Error calculating dashboard metrics: {e}")
            raise

    def _count_executions_by_status(self) -> dict[str, int]:
        """Conta execuções por status."""
        rows = (
            self.db.query(Execucao.status, func.count(Execucao.id).label("count"))
            .group_by(Execucao.status)
            .all()
        )

        counts: dict[str, int] = {row.status.value: row.count for row in rows}

        active_statuses = [
            ExecucaoStatus.AGUARDANDO.value,
            ExecucaoStatus.EM_EXECUCAO.value,
            ExecucaoStatus.PAUSADO.value,
        ]

        failed_statuses = [
            ExecucaoStatus.FALHOU.value,
            ExecucaoStatus.CONCLUIDO_COM_ERROS.value,
        ]

        return {
            "total": sum(counts.values()),
            "active": sum(counts.get(s, 0) for s in active_statuses),
            "completed": counts.get(ExecucaoStatus.CONCLUIDO.value, 0),
            "failed": sum(counts.get(s, 0) for s in failed_statuses),
            "pending": counts.get(ExecucaoStatus.AGUARDANDO.value, 0),
        }

    def _count_processes(self) -> dict[str, int]:
        """Conta processos e processos com agendamento recorrente."""
        total = self.db.query(func.count(Processo.id)).scalar() or 0

        # Processos que têm pelo menos uma configuração recorrente
        scheduled = (
            self.db.query(func.count(func.distinct(Configuracao.processo_id)))
            .filter(Configuracao.agendamento_tipo == AgendamentoTipo.RECORRENTE)
            .scalar()
            or 0
        )

        return {
            "total": total,
            "with_schedule": scheduled,
        }

    def _calculate_success_rate(self, last_n: int = 100) -> float:
        """Calcula taxa de sucesso das últimas N execuções (%)."""
        rows = (
            self.db.query(Execucao.status)
            .order_by(Execucao.created_at.desc())
            .limit(last_n)
            .all()
        )

        if not rows:
            return 0.0

        succeeded = sum(1 for row in rows if row.status == ExecucaoStatus.CONCLUIDO)
        rate = (succeeded / len(rows)) * 100
        return round(rate, 2)

    def _calculate_avg_duration(self) -> float:
        """Calcula duração média das execuções concluídas (minutos) via SQL."""
        from sqlalchemy import Float, cast

        avg_seconds = (
            self.db.query(
                func.avg(
                    cast(
                        func.julianday(Execucao.finalizado_em)
                        - func.julianday(Execucao.iniciado_em),
                        Float,
                    )
                    * 86400
                )
            )
            .filter(
                Execucao.status == ExecucaoStatus.CONCLUIDO,
                Execucao.finalizado_em.isnot(None),
                Execucao.iniciado_em.isnot(None),
            )
            .scalar()
        )

        if not avg_seconds:
            return 0.0

        return round(avg_seconds / 60, 2)

    def _get_recent_activity(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retorna as últimas N execuções com nome do processo via JOIN."""
        from sqlalchemy.orm import joinedload

        execucoes = (
            self.db.query(Execucao)
            .options(joinedload(Execucao.processo))
            .order_by(Execucao.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for execucao in execucoes:
            processo_nome = "N/A"
            try:
                if execucao.processo:
                    processo_nome = execucao.processo.nome
            except Exception:
                pass

            result.append(
                {
                    "id": str(execucao.id),
                    "processo_nome": processo_nome,
                    "status": execucao.status.value,
                    "created_at": execucao.created_at.isoformat()
                    if execucao.created_at
                    else None,
                }
            )

        return result
