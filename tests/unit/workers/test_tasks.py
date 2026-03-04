"""
Testes unitários para as tasks Celery (execucao, agendamento, limpeza).
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Import tasks so they register in celery_app
import toninho.workers.tasks.execucao_task  # noqa: F401
import toninho.workers.tasks.agendamento_task  # noqa: F401
import toninho.workers.tasks.limpeza_task  # noqa: F401

from toninho.models import Base, Configuracao, Execucao, Processo
from toninho.models.enums import (
    AgendamentoTipo,
    ExecucaoStatus,
    FormatoSaida,
)


# ──────────────────────────────────────────────────────── fixtures ────────────

@pytest.fixture(scope="module")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db(engine) -> Session:
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def processo(db):
    p = Processo(nome=f"Proc {uuid.uuid4().hex[:6]}", descricao="test")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def execucao(db, processo):
    e = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def configuracao_recorrente(db, processo, tmp_path):
    c = Configuracao(
        processo_id=processo.id,
        urls=["https://example.com"],
        timeout=30,
        max_retries=1,
        formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
        output_dir=str(tmp_path),
        agendamento_tipo=AgendamentoTipo.RECORRENTE,
        agendamento_cron="* * * * *",  # Todo minuto
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ──────────────────────────────────────────────── execucao_task tests ────────

class TestExecutarProcessoTask:
    """Testes para executar_processo_task."""

    def test_task_is_registered(self):
        """Task deve estar registrada no celery_app."""
        from toninho.workers.celery_app import celery_app
        task_names = list(celery_app.tasks.keys())
        assert any("executar_processo" in t for t in task_names)

    def test_task_apply_calls_orchestrator(self, db, execucao):
        """apply() deve chamar ExtractionOrchestrator.run()."""
        from toninho.workers.tasks.execucao_task import executar_processo_task

        mock_resultado = {
            "status": ExecucaoStatus.CONCLUIDO,
            "paginas_sucesso": 1,
            "paginas_falha": 0,
            "total": 1,
            "bytes_extraidos": 512,
        }

        # SessionLocal is imported lazily inside the task — patch at source
        with patch("toninho.core.database.SessionLocal", return_value=db), \
             patch("toninho.workers.utils.ExtractionOrchestrator.run", return_value=mock_resultado):
            result = executar_processo_task.apply(args=[str(execucao.id)])

        assert result.get()["status"] == "concluido"

    def test_task_result_has_required_keys(self, db, execucao):
        """Resultado da task deve ter status, paginas_sucesso, paginas_falha, total, bytes."""
        from toninho.workers.tasks.execucao_task import executar_processo_task

        mock_resultado = {
            "status": ExecucaoStatus.CONCLUIDO,
            "paginas_sucesso": 2,
            "paginas_falha": 0,
            "total": 2,
            "bytes_extraidos": 1024,
        }

        with patch("toninho.core.database.SessionLocal", return_value=db), \
             patch("toninho.workers.utils.ExtractionOrchestrator.run", return_value=mock_resultado):
            result = executar_processo_task.apply(args=[str(execucao.id)])

        data = result.get()
        assert all(k in data for k in ("status", "paginas_sucesso", "paginas_falha", "total", "bytes_extraidos"))

    def test_task_handles_value_error_without_retry(self, db, execucao):
        """ValueError (erro de negócio) não deve causar retry."""
        from toninho.workers.tasks.execucao_task import executar_processo_task

        with patch("toninho.core.database.SessionLocal", return_value=db), \
             patch("toninho.workers.utils.ExtractionOrchestrator.run", side_effect=ValueError("bad data")):
            with pytest.raises(ValueError):
                executar_processo_task.apply(args=[str(execucao.id)]).get()


# ──────────────────────────────────────────── agendamento_task tests ─────────

class TestVerificarAgendamentos:
    """Testes para verificar_agendamentos task."""

    def test_task_is_registered(self):
        from toninho.workers.celery_app import celery_app
        task_names = list(celery_app.tasks.keys())
        assert any("verificar_agendamentos" in t for t in task_names)

    def test_task_name_matches_beat_schedule(self):
        """Nome da task deve corresponder EXATAMENTE ao definido no beat_schedule.

        BUG-001: mismatch causava KeyError no worker a cada 60s.
        """
        from toninho.workers.celery_app import celery_app
        from toninho.workers.tasks.agendamento_task import verificar_agendamentos

        expected_name = "toninho.workers.tasks.agendamento_task.verificar_agendamentos"
        beat_task_name = celery_app.conf.beat_schedule["verificar-agendamentos"]["task"]

        assert verificar_agendamentos.name == expected_name, (
            f"Task name '{verificar_agendamentos.name}' difere do esperado '{expected_name}'"
        )
        assert verificar_agendamentos.name == beat_task_name, (
            f"Task name '{verificar_agendamentos.name}' difere do beat_schedule '{beat_task_name}'"
        )

    def test_returns_execucoes_criadas(self, db, configuracao_recorrente):
        """Deve retornar contagem de execuções criadas."""
        from toninho.workers.tasks.agendamento_task import verificar_agendamentos
        from toninho.workers.tasks.execucao_task import executar_processo_task

        with patch("toninho.core.database.SessionLocal", return_value=db), \
             patch.object(executar_processo_task, "delay"):
            result = verificar_agendamentos.apply()

        data = result.get()
        assert "execucoes_criadas" in data
        assert isinstance(data["execucoes_criadas"], int)

    def test_no_execucao_created_when_no_recorrente_config(self, db, processo):
        """Sem configurações RECORRENTE, não deve criar execuções."""
        from toninho.workers.tasks.agendamento_task import verificar_agendamentos

        # Configuração MANUAL — não deve disparar
        config = Configuracao(
            processo_id=processo.id,
            urls=["https://example.com"],
            timeout=30,
            max_retries=1,
            formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
            output_dir="./output",
            agendamento_tipo=AgendamentoTipo.MANUAL,
        )
        db.add(config)
        db.commit()

        with patch("toninho.core.database.SessionLocal", return_value=db):
            result = verificar_agendamentos.apply()

        data = result.get()
        assert data["execucoes_criadas"] == 0

    def test_avoids_duplicate_execucoes(self, db, configuracao_recorrente, processo):
        """Não deve criar execução duplicada se já há uma recente."""
        from toninho.workers.tasks.agendamento_task import verificar_agendamentos

        # Criar execução recente
        execucao_recente = Execucao(
            processo_id=processo.id,
            status=ExecucaoStatus.CRIADO,
        )
        # Simular criação recente
        db.add(execucao_recente)
        db.commit()

        with patch("toninho.core.database.SessionLocal", return_value=db):
            result = verificar_agendamentos.apply()

        data = result.get()
        # Devido à execução recente, não deve criar outra
        assert data["execucoes_criadas"] == 0


# ──────────────────────────────────────────────── limpeza_task tests ─────────

class TestLimparLogsAntigos:
    """Testes para limpar_logs_antigos task."""

    def test_task_is_registered(self):
        from toninho.workers.celery_app import celery_app
        task_names = list(celery_app.tasks.keys())
        assert any("limpar_logs_antigos" in t for t in task_names)

    def test_task_name_matches_beat_schedule(self):
        """Nome da task deve corresponder EXATAMENTE ao definido no beat_schedule.

        Mesmo padrão do BUG-001: alinha nome do decorator com beat_schedule.
        """
        from toninho.workers.celery_app import celery_app
        from toninho.workers.tasks.limpeza_task import limpar_logs_antigos

        expected_name = "toninho.workers.tasks.limpeza_task.limpar_logs_antigos"
        beat_task_name = celery_app.conf.beat_schedule["limpar-logs-antigos"]["task"]

        assert limpar_logs_antigos.name == expected_name
        assert limpar_logs_antigos.name == beat_task_name

    def test_limpar_logs_retorna_deleted_count(self, db, execucao):
        """Deve retornar logs_deletados e dias_retencao."""
        from toninho.workers.tasks.limpeza_task import limpar_logs_antigos
        from toninho.models.log import Log
        from toninho.models.enums import LogNivel

        # Criar logs antigos (40 dias atrás)
        data_antiga = datetime.now(timezone.utc) - timedelta(days=40)
        for i in range(3):
            log = Log(
                execucao_id=execucao.id,
                nivel=LogNivel.INFO,
                mensagem=f"Log antigo {i}",
                timestamp=data_antiga,
            )
            db.add(log)
        db.commit()

        with patch("toninho.core.database.SessionLocal", return_value=db):
            result = limpar_logs_antigos.apply(kwargs={"dias_retencao": 30})

        data = result.get()
        assert "logs_deletados" in data
        assert data["logs_deletados"] >= 3
        assert data["dias_retencao"] == 30

    def test_limpar_logs_keeps_recent_logs(self, db, execucao):
        """Logs recentes não devem ser deletados."""
        from toninho.workers.tasks.limpeza_task import limpar_logs_antigos
        from toninho.models.log import Log
        from toninho.models.enums import LogNivel

        # Salvar id antes — execucao pode ser detached após o task fechar a sessão
        execucao_id = execucao.id

        # Criar log recente
        log = Log(
            execucao_id=execucao_id,
            nivel=LogNivel.INFO,
            mensagem="Log recente",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()

        with patch("toninho.core.database.SessionLocal", return_value=db):
            result = limpar_logs_antigos.apply(kwargs={"dias_retencao": 30})

        db.expire_all()
        after_count = db.query(Log).filter(Log.execucao_id == execucao_id).count()

        # Log recente deve estar intacto
        assert after_count >= 1

    def test_limpar_logs_default_retention(self, db):
        """Deve usar 30 dias como default de retenção."""
        from toninho.workers.tasks.limpeza_task import limpar_logs_antigos

        with patch("toninho.core.database.SessionLocal", return_value=db):
            result = limpar_logs_antigos.apply()

        data = result.get()
        assert data["dias_retencao"] == 30
