"""Testes para o MetricsService."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from toninho.models.configuracao import Configuracao
from toninho.models.enums import (
    AgendamentoTipo,
    ExecucaoStatus,
    FormatoSaida,
    VolumeStatus,
    VolumeTipo,
)
from toninho.models.execucao import Execucao
from toninho.models.processo import Processo
from toninho.models.volume import Volume
from toninho.monitoring.metrics import MetricsService


@pytest.fixture
def processo(db: Session) -> Processo:
    p = Processo(nome="Processo Teste", descricao="Desc")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def execucao_concluida(db: Session, processo: Processo) -> Execucao:
    now = datetime.now(UTC)
    e = Execucao(
        processo_id=processo.id,
        status=ExecucaoStatus.CONCLUIDO,
        iniciado_em=now - timedelta(minutes=5),
        finalizado_em=now,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def execucao_falhou(db: Session, processo: Processo) -> Execucao:
    e = Execucao(
        processo_id=processo.id,
        status=ExecucaoStatus.FALHOU,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


class TestMetricsService:
    """Testes para o MetricsService."""

    def test_get_dashboard_metrics_structure(self, db: Session):
        """Retorna estrutura correta do dashboard."""
        service = MetricsService(db=db)
        result = service.get_dashboard_metrics()

        assert "executions" in result
        assert "processes" in result
        assert "success_rate" in result
        assert "avg_duration_minutes" in result
        assert "recent_activity" in result

    def test_count_executions_empty(self, db: Session):
        """Conta zero execuções quando banco vazio."""
        service = MetricsService(db=db)
        result = service._count_executions_by_status()

        assert result["total"] == 0
        assert result["active"] == 0
        assert result["completed"] == 0
        assert result["failed"] == 0
        assert result["pending"] == 0

    def test_count_executions_with_data(
        self, db: Session, execucao_concluida: Execucao, execucao_falhou: Execucao
    ):
        """Conta execuções por status corretamente."""
        service = MetricsService(db=db)
        result = service._count_executions_by_status()

        assert result["total"] == 2
        assert result["completed"] == 1
        assert result["failed"] == 1

    def test_count_executions_active_statuses(self, db: Session, processo: Processo):
        """Conta execuções ativas (AGUARDANDO, EM_EXECUCAO, PAUSADO)."""
        for status in [ExecucaoStatus.AGUARDANDO, ExecucaoStatus.EM_EXECUCAO]:
            e = Execucao(processo_id=processo.id, status=status)
            db.add(e)
        db.commit()

        service = MetricsService(db=db)
        result = service._count_executions_by_status()

        assert result["active"] == 2
        assert result["pending"] == 1

    def test_count_processes_empty(self, db: Session):
        """Conta zero processos quando banco vazio."""
        service = MetricsService(db=db)
        result = service._count_processes()

        assert result["total"] == 0
        assert result["with_schedule"] == 0

    def test_count_processes_with_schedule(self, db: Session):
        """Conta processos com agendamento recorrente."""
        p = Processo(nome="P1", descricao="desc")
        db.add(p)
        db.commit()
        db.refresh(p)

        v = Volume(
            nome="Vol Metrics Schedule",
            path="/tmp/metrics-schedule",
            tipo=VolumeTipo.LOCAL,
            status=VolumeStatus.ATIVO,
        )
        db.add(v)
        db.commit()
        db.refresh(v)

        c = Configuracao(
            processo_id=p.id,
            urls=["https://example.com"],
            agendamento_tipo=AgendamentoTipo.RECORRENTE,
            agendamento_cron="0 * * * *",
            formato_saida=FormatoSaida.ARQUIVO_UNICO,
            volume_id=v.id,
        )
        db.add(c)
        db.commit()

        service = MetricsService(db=db)
        result = service._count_processes()

        assert result["total"] == 1
        assert result["with_schedule"] == 1

    def test_count_processes_without_schedule(self, db: Session, processo: Processo):
        """Processo sem agendamento não conta em with_schedule."""
        v = Volume(
            nome="Vol Metrics NoSchedule",
            path="/tmp/metrics-nosched",
            tipo=VolumeTipo.LOCAL,
            status=VolumeStatus.ATIVO,
        )
        db.add(v)
        db.commit()
        db.refresh(v)

        c = Configuracao(
            processo_id=processo.id,
            urls=["https://example.com"],
            agendamento_tipo=AgendamentoTipo.MANUAL,
            formato_saida=FormatoSaida.ARQUIVO_UNICO,
            volume_id=v.id,
        )
        db.add(c)
        db.commit()

        service = MetricsService(db=db)
        result = service._count_processes()

        assert result["total"] == 1
        assert result["with_schedule"] == 0

    def test_success_rate_empty_db(self, db: Session):
        """Taxa de sucesso é 0 quando não há execuções."""
        service = MetricsService(db=db)
        result = service._calculate_success_rate()

        assert result == 0.0

    def test_success_rate_all_success(self, db: Session, execucao_concluida: Execucao):
        """Taxa de sucesso é 100% quando tudo concluiu."""
        service = MetricsService(db=db)
        result = service._calculate_success_rate()

        assert result == 100.0

    def test_success_rate_mixed(
        self, db: Session, execucao_concluida: Execucao, execucao_falhou: Execucao
    ):
        """Taxa de sucesso calculada corretamente para resultado misto."""
        service = MetricsService(db=db)
        result = service._calculate_success_rate()

        assert result == 50.0

    def test_avg_duration_empty_db(self, db: Session):
        """Duração média é 0 quando não há execuções concluídas."""
        service = MetricsService(db=db)
        result = service._calculate_avg_duration()

        assert result == 0.0

    def test_avg_duration_with_data(self, db: Session, execucao_concluida: Execucao):
        """Duração média calculada corretamente."""
        service = MetricsService(db=db)
        result = service._calculate_avg_duration()

        # 5 minutos esperado
        assert result > 0
        assert result <= 10.0  # Tolerância

    def test_avg_duration_ignores_failed(
        self, db: Session, execucao_concluida: Execucao, execucao_falhou: Execucao
    ):
        """Duração média ignora execuções não-concluídas."""
        service = MetricsService(db=db)
        result = service._calculate_avg_duration()

        # Deve ser calculada apenas com execucao_concluida
        assert result > 0

    def test_recent_activity_empty(self, db: Session):
        """Retorna lista vazia quando sem execuções."""
        service = MetricsService(db=db)
        result = service._get_recent_activity()

        assert result == []

    def test_recent_activity_structure(self, db: Session, execucao_concluida: Execucao):
        """Atividade recente retorna estrutura correta."""
        service = MetricsService(db=db)
        result = service._get_recent_activity()

        assert len(result) == 1
        item = result[0]
        assert "id" in item
        assert "status" in item
        assert "created_at" in item
        assert item["status"] == ExecucaoStatus.CONCLUIDO.value

    def test_recent_activity_limit(self, db: Session, processo: Processo):
        """Respeita o limite de atividades recentes."""
        for i in range(15):
            e = Execucao(
                processo_id=processo.id,
                status=ExecucaoStatus.CONCLUIDO,
            )
            db.add(e)
        db.commit()

        service = MetricsService(db=db)
        result = service._get_recent_activity(limit=5)

        assert len(result) == 5
