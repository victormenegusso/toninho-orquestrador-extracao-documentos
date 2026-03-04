"""Testes unitários para LogRepository."""

from uuid import uuid4

import pytest

from toninho.models.enums import ExecucaoStatus, LogNivel
from toninho.models.execucao import Execucao
from toninho.models.log import Log
from toninho.models.processo import Processo
from toninho.repositories.log_repository import LogRepository


class TestLogRepository:
    """Testes para LogRepository."""

    @pytest.fixture
    def repository(self):
        return LogRepository()

    @pytest.fixture
    def processo(self, db):
        p = Processo(nome="Processo Log Repo Teste", descricao="desc")
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
    # create
    # ------------------------------------------------------------------

    def test_create(self, db, repository, execucao):
        log = Log(
            execucao_id=execucao.id,
            nivel=LogNivel.INFO,
            mensagem="Log de criação",
        )
        result = repository.create(db, log)

        assert result.id is not None
        assert result.execucao_id == execucao.id
        assert result.nivel == LogNivel.INFO
        assert result.mensagem == "Log de criação"

    def test_create_com_contexto(self, db, repository, execucao):
        log = Log(
            execucao_id=execucao.id,
            nivel=LogNivel.DEBUG,
            mensagem="Log com contexto",
            contexto={"url": "https://exemplo.com", "status_code": 200},
        )
        result = repository.create(db, log)

        assert result.contexto == {"url": "https://exemplo.com", "status_code": 200}

    # ------------------------------------------------------------------
    # create_batch
    # ------------------------------------------------------------------

    def test_create_batch(self, db, repository, execucao):
        logs = [
            Log(execucao_id=execucao.id, nivel=LogNivel.INFO, mensagem=f"Log {i}")
            for i in range(3)
        ]
        result = repository.create_batch(db, logs)

        assert len(result) == 3
        for log in result:
            assert log.id is not None

    def test_create_batch_vazio(self, db, repository):
        result = repository.create_batch(db, [])
        assert result == []

    # ------------------------------------------------------------------
    # get_by_id
    # ------------------------------------------------------------------

    def test_get_by_id_encontrado(self, db, repository, log_factory):
        log = log_factory()
        result = repository.get_by_id(db, log.id)

        assert result is not None
        assert result.id == log.id

    def test_get_by_id_nao_encontrado(self, db, repository):
        result = repository.get_by_id(db, uuid4())
        assert result is None

    # ------------------------------------------------------------------
    # get_by_execucao_id
    # ------------------------------------------------------------------

    def test_get_by_execucao_id_sem_filtro(self, db, repository, log_factory):
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.WARNING)
        log_factory(nivel=LogNivel.ERROR)

        result, total = repository.get_by_execucao_id(
            db,
            log_factory.__self__.execucao.id
            if hasattr(log_factory, "__self__")
            else uuid4(),
        )
        # Use execucao from fixture differently
        result, total = repository.get_by_execucao_id(
            db, db.query(Log).first().execucao_id
        )
        assert total == 3

    def test_get_by_execucao_id_com_filtro_nivel(
        self, db, repository, log_factory, execucao
    ):
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.ERROR)

        result, total = repository.get_by_execucao_id(
            db, execucao.id, nivel=LogNivel.INFO
        )
        assert total == 2
        assert all(log.nivel == LogNivel.INFO for log in result)

    def test_get_by_execucao_id_com_filtro_busca(
        self, db, repository, log_factory, execucao
    ):
        log_factory(mensagem="Página extraída com sucesso")
        log_factory(mensagem="Erro ao acessar URL")

        result, total = repository.get_by_execucao_id(db, execucao.id, busca="extraída")
        assert total == 1
        assert result[0].mensagem == "Página extraída com sucesso"

    def test_get_by_execucao_id_paginacao(self, db, repository, log_factory, execucao):
        for _ in range(5):
            log_factory()

        result, total = repository.get_by_execucao_id(db, execucao.id, skip=0, limit=3)
        assert total == 5
        assert len(result) == 3

    def test_get_by_execucao_id_sem_logs(self, db, repository, execucao):
        result, total = repository.get_by_execucao_id(db, execucao.id)
        assert total == 0
        assert result == []

    # ------------------------------------------------------------------
    # get_recent
    # ------------------------------------------------------------------

    def test_get_recent_retorna_n_logs(self, db, repository, log_factory, execucao):
        for i in range(5):
            log_factory(mensagem=f"Log {i}")

        result = repository.get_recent(db, execucao.id, limit=3)
        assert len(result) == 3

    def test_get_recent_sem_logs(self, db, repository, execucao):
        result = repository.get_recent(db, execucao.id)
        assert result == []

    # ------------------------------------------------------------------
    # count_by_nivel
    # ------------------------------------------------------------------

    def test_count_by_nivel(self, db, repository, log_factory, execucao):
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.ERROR)
        log_factory(nivel=LogNivel.DEBUG)

        result = repository.count_by_nivel(db, execucao.id)

        assert result[LogNivel.INFO] == 2
        assert result[LogNivel.ERROR] == 1
        assert result[LogNivel.DEBUG] == 1
        assert result[LogNivel.WARNING] == 0

    def test_count_by_nivel_sem_logs(self, db, repository, execucao):
        result = repository.count_by_nivel(db, execucao.id)
        assert all(v == 0 for v in result.values())

    # ------------------------------------------------------------------
    # delete_by_execucao_id
    # ------------------------------------------------------------------

    def test_delete_by_execucao_id(self, db, repository, log_factory, execucao):
        log_factory()
        log_factory()

        count = repository.delete_by_execucao_id(db, execucao.id)
        assert count == 2

        _, total = repository.get_by_execucao_id(db, execucao.id)
        assert total == 0

    def test_delete_by_execucao_id_sem_logs(self, db, repository, execucao):
        count = repository.delete_by_execucao_id(db, execucao.id)
        assert count == 0
