"""
Testes unitários para ExtractionOrchestrator.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from toninho.models import Base, Configuracao, Execucao, Processo
from toninho.models.enums import (
    AgendamentoTipo,
    ExecucaoStatus,
    FormatoSaida,
    LogNivel,
    PaginaStatus,
)
from toninho.workers.utils import ExtractionOrchestrator


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
    p = Processo(nome=f"Teste {uuid.uuid4().hex[:6]}", descricao="desc")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def configuracao(db, processo, tmp_path):
    c = Configuracao(
        processo_id=processo.id,
        urls=["https://example.com/a", "https://example.com/b"],
        timeout=30,
        max_retries=1,
        formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
        output_dir=str(tmp_path),
        agendamento_tipo=AgendamentoTipo.MANUAL,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def execucao(db, processo):
    e = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def mock_storage(tmp_path):
    from toninho.extraction.storage import LocalFileSystemStorage
    return LocalFileSystemStorage(base_dir=str(tmp_path))


# ─────────────────────────────────────────── ExtractionOrchestrator tests ────

SUCESSO_RESULT = {
    "status": "sucesso",
    "url": "https://example.com/a",
    "path": "/tmp/a.md",
    "bytes": 1024,
    "title": "Test",
    "from_cache": False,
    "error": None,
}

ERRO_RESULT = {
    "status": "erro",
    "url": "https://example.com/b",
    "path": None,
    "bytes": 0,
    "title": "",
    "from_cache": False,
    "error": "Connection refused",
}


class TestExtractionOrchestratorSuccess:
    """Testes com extração bem-sucedida."""

    def test_run_updates_status_to_em_execucao_then_concluido(
        self, db, execucao, configuracao, mock_storage
    ):
        """Após run(), execução deve estar CONCLUIDO."""
        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT

            orch = ExtractionOrchestrator(db, storage=mock_storage)
            resultado = orch.run(execucao.id)

        db.refresh(execucao)
        assert resultado["status"] == ExecucaoStatus.CONCLUIDO
        assert execucao.status == ExecucaoStatus.CONCLUIDO

    def test_run_counts_sucesso_pages(self, db, processo, configuracao, mock_storage):
        """Deve contar corretamente as páginas de sucesso."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT

            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        assert resultado["paginas_sucesso"] == 2  # 2 URLs
        assert resultado["paginas_falha"] == 0
        assert resultado["total"] == 2

    def test_run_sets_iniciado_em(self, db, processo, configuracao, mock_storage):
        """iniciado_em deve ser preenchido após run()."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        db.refresh(execucao)
        assert execucao.iniciado_em is not None

    def test_run_sets_finalizado_em(self, db, processo, configuracao, mock_storage):
        """finalizado_em deve ser preenchido após run()."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        db.refresh(execucao)
        assert execucao.finalizado_em is not None

    def test_run_updates_bytes_extraidos(self, db, processo, configuracao, mock_storage):
        """bytes_extraidos deve ser acumulado."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT
            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        # 2 URLs × 1024 bytes = 2048
        assert resultado["bytes_extraidos"] == 2048

    def test_run_creates_paginas_extraidas(self, db, processo, configuracao, mock_storage):
        """Deve criar registros de PaginaExtraida para cada URL."""
        from toninho.models.pagina_extraida import PaginaExtraida

        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        paginas = db.query(PaginaExtraida).filter(PaginaExtraida.execucao_id == execucao.id).all()
        assert len(paginas) == 2
        assert all(p.status == PaginaStatus.SUCESSO for p in paginas)

    def test_run_creates_logs(self, db, processo, configuracao, mock_storage):
        """Deve criar logs INFO durante a extração."""
        from toninho.models.log import Log

        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        logs = db.query(Log).filter(Log.execucao_id == execucao.id).all()
        assert len(logs) >= 1  # Log inicial + final no mínimo


class TestExtractionOrchestratorMixedResults:
    """Testes com resultados mistos (sucesso + erro)."""

    def test_run_concluido_com_erros_when_partial_failure(
        self, db, processo, configuracao, mock_storage
    ):
        """Status CONCLUIDO_COM_ERROS quando há mistura de sucesso e erro."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        side_effects = [SUCESSO_RESULT, ERRO_RESULT]

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = side_effects
            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        assert resultado["status"] == ExecucaoStatus.CONCLUIDO_COM_ERROS
        assert resultado["paginas_sucesso"] == 1
        assert resultado["paginas_falha"] == 1

    def test_run_falhou_when_all_fail(self, db, processo, configuracao, mock_storage):
        """Status FALHOU quando todas as extrações falham."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ERRO_RESULT
            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        assert resultado["status"] == ExecucaoStatus.FALHOU
        assert resultado["paginas_falha"] == 2


class TestExtractionOrchestratorEdgeCases:
    """Testes de casos especiais."""

    def test_run_raises_when_execucao_not_found(self, db, mock_storage):
        """run() deve levantar ValueError se execução não existe."""
        orch = ExtractionOrchestrator(db, storage=mock_storage)
        with pytest.raises(ValueError, match="não encontrada"):
            orch.run(uuid.uuid4())

    def test_run_falhou_when_no_configuracao(self, db, processo, mock_storage):
        """run() deve retornar FALHOU se processo não tem configuração."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        resultado = ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        assert resultado["status"] == ExecucaoStatus.FALHOU
        db.refresh(execucao)
        assert execucao.status == ExecucaoStatus.FALHOU

    def test_run_zero_taxa_erro_on_full_success(self, db, processo, configuracao, mock_storage):
        """taxa_erro deve ser 0.0 quando todas as extrações têm sucesso."""
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        db.refresh(execucao)
        assert execucao.taxa_erro == 0.0

    def test_logs_tem_contexto_preenchido(self, db, processo, configuracao, mock_storage):
        """Todos os logs de extração devem ter contexto preenchido (MH-001)."""
        from toninho.models.log import Log

        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        with patch.object(ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = SUCESSO_RESULT
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        logs = db.query(Log).filter(Log.execucao_id == execucao.id).all()
        assert len(logs) > 0, "Nenhum log criado"

        logs_sem_contexto = [l for l in logs if l.contexto is None]
        assert not logs_sem_contexto, (
            f"Logs sem contexto: {[l.mensagem for l in logs_sem_contexto]}"
        )

    def test_add_log_aceita_contexto(self, db, processo, mock_storage):
        """_add_log deve persistir o contexto fornecido (MH-001)."""
        from toninho.models.log import Log

        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        ctx = {"url": "https://example.com", "indice": 1, "total": 3}
        ExtractionOrchestrator._add_log(db, execucao.id, LogNivel.INFO, "teste contexto", contexto=ctx)
        db.commit()

        log = db.query(Log).filter(Log.execucao_id == execucao.id).order_by(Log.timestamp.desc()).first()
        assert log is not None
        assert log.contexto == ctx
