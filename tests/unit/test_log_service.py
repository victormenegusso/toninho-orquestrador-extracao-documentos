"""Testes unitários para LogService."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from toninho.core.exceptions import NotFoundError
from toninho.models.enums import ExecucaoStatus, LogNivel
from toninho.models.execucao import Execucao
from toninho.models.log import Log
from toninho.models.processo import Processo
from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.log_repository import LogRepository
from toninho.schemas.log import LogCreate, LogFilter
from toninho.services.log_service import LogService


class TestLogService:
    """Testes para LogService."""

    @pytest.fixture
    def service(self):
        return LogService(
            repository=LogRepository(),
            execucao_repository=ExecucaoRepository(),
        )

    @pytest.fixture
    def processo(self, db):
        p = Processo(nome="Processo Log Svc Teste", descricao="desc")
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    @pytest.fixture
    def execucao(self, db, processo):
        e = Execucao(processo_id=processo.id, status=ExecucaoStatus.EM_EXECUCAO)
        db.add(e)
        db.commit()
        db.refresh(e)
        return e

    @pytest.fixture
    def log_factory(self, db, execucao):
        def _create(**kwargs):
            defaults = {
                "execucao_id": execucao.id,
                "nivel": LogNivel.INFO,
                "mensagem": "Mensagem de teste",
            }
            defaults.update(kwargs)
            log = Log(**defaults)
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        return _create

    # ------------------------------------------------------------------
    # create_log
    # ------------------------------------------------------------------

    def test_create_log_sucesso(self, db, service, execucao):
        log_create = LogCreate(
            execucao_id=execucao.id,
            nivel=LogNivel.INFO,
            mensagem="Log de teste",
        )
        result = service.create_log(db, log_create)

        assert result.id is not None
        assert result.execucao_id == execucao.id
        assert result.nivel == LogNivel.INFO
        assert result.mensagem == "Log de teste"

    def test_create_log_com_contexto(self, db, service, execucao):
        log_create = LogCreate(
            execucao_id=execucao.id,
            nivel=LogNivel.DEBUG,
            mensagem="Log debug",
            contexto={"url": "https://teste.com"},
        )
        result = service.create_log(db, log_create)
        assert result.contexto == {"url": "https://teste.com"}

    def test_create_log_execucao_inexistente(self, db, service):
        log_create = LogCreate(
            execucao_id=uuid4(),
            nivel=LogNivel.INFO,
            mensagem="Log",
        )
        with pytest.raises(NotFoundError):
            service.create_log(db, log_create)

    # ------------------------------------------------------------------
    # create_log_batch
    # ------------------------------------------------------------------

    def test_create_log_batch_sucesso(self, db, service, execucao):
        logs_create = [
            LogCreate(execucao_id=execucao.id, nivel=LogNivel.INFO, mensagem=f"Log {i}")
            for i in range(3)
        ]
        result = service.create_log_batch(db, logs_create)
        assert len(result) == 3

    def test_create_log_batch_execucao_inexistente(self, db, service, execucao):
        logs_create = [
            LogCreate(execucao_id=execucao.id, nivel=LogNivel.INFO, mensagem="Log 1"),
            LogCreate(execucao_id=uuid4(), nivel=LogNivel.INFO, mensagem="Log 2"),
        ]
        with pytest.raises(NotFoundError):
            service.create_log_batch(db, logs_create)

    # ------------------------------------------------------------------
    # get_log
    # ------------------------------------------------------------------

    def test_get_log_sucesso(self, db, service, log_factory):
        log = log_factory()
        result = service.get_log(db, log.id)
        assert result.id == log.id

    def test_get_log_nao_encontrado(self, db, service):
        with pytest.raises(NotFoundError):
            service.get_log(db, uuid4())

    # ------------------------------------------------------------------
    # list_logs_by_execucao
    # ------------------------------------------------------------------

    def test_list_logs_by_execucao_sem_filtro(self, db, service, log_factory, execucao):
        log_factory()
        log_factory()

        result = service.list_logs_by_execucao(db, execucao.id)

        assert result.meta.total == 2
        assert len(result.data) == 2

    def test_list_logs_by_execucao_com_filtro_nivel(self, db, service, log_factory, execucao):
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.ERROR)

        filtro = LogFilter(nivel=LogNivel.INFO)
        result = service.list_logs_by_execucao(db, execucao.id, filtro=filtro)

        assert result.meta.total == 1
        assert result.data[0].nivel == LogNivel.INFO

    def test_list_logs_by_execucao_com_busca(self, db, service, log_factory, execucao):
        log_factory(mensagem="Página extraída")
        log_factory(mensagem="Erro na URL")

        filtro = LogFilter(busca="extraída")
        result = service.list_logs_by_execucao(db, execucao.id, filtro=filtro)

        assert result.meta.total == 1

    def test_list_logs_by_execucao_paginacao(self, db, service, log_factory, execucao):
        for _ in range(5):
            log_factory()

        result = service.list_logs_by_execucao(db, execucao.id, page=1, per_page=3)

        assert result.meta.total == 5
        assert len(result.data) == 3
        assert result.meta.page == 1
        assert result.meta.total_pages == 2

    def test_list_logs_by_execucao_execucao_inexistente(self, db, service):
        with pytest.raises(NotFoundError):
            service.list_logs_by_execucao(db, uuid4())

    # ------------------------------------------------------------------
    # get_logs_recentes
    # ------------------------------------------------------------------

    def test_get_logs_recentes(self, db, service, log_factory, execucao):
        for i in range(5):
            log_factory(mensagem=f"Log {i}")

        result = service.get_logs_recentes(db, execucao.id, limit=3)
        assert len(result) == 3

    def test_get_logs_recentes_execucao_inexistente(self, db, service):
        with pytest.raises(NotFoundError):
            service.get_logs_recentes(db, uuid4())

    # ------------------------------------------------------------------
    # get_estatisticas_logs
    # ------------------------------------------------------------------

    def test_get_estatisticas_logs(self, db, service, log_factory, execucao):
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.ERROR)

        result = service.get_estatisticas_logs(db, execucao.id)

        assert result.execucao_id == execucao.id
        assert result.total == 3
        assert result.por_nivel[LogNivel.INFO] == 2
        assert result.por_nivel[LogNivel.ERROR] == 1
        assert result.percentual_erros == pytest.approx(33.33, abs=0.01)
        assert result.primeiro_log is not None
        assert result.ultimo_log is not None

    def test_get_estatisticas_logs_sem_logs(self, db, service, execucao):
        result = service.get_estatisticas_logs(db, execucao.id)

        assert result.total == 0
        assert result.percentual_erros == 0.0
        assert result.primeiro_log is None
        assert result.ultimo_log is None

    def test_get_estatisticas_logs_execucao_inexistente(self, db, service):
        with pytest.raises(NotFoundError):
            service.get_estatisticas_logs(db, uuid4())
