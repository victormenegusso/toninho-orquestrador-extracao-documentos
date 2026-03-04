"""Testes unitários para ExecucaoRepository."""

from uuid import uuid4

import pytest

from toninho.models.enums import ExecucaoStatus
from toninho.models.execucao import Execucao
from toninho.models.processo import Processo
from toninho.repositories.execucao_repository import ExecucaoRepository


class TestExecucaoRepository:
    """Testes para ExecucaoRepository."""

    @pytest.fixture
    def repository(self):
        return ExecucaoRepository()

    @pytest.fixture
    def processo(self, db):
        p = Processo(nome="Processo Exe Repo Teste", descricao="desc")
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    @pytest.fixture
    def execucao_factory(self, db, processo):
        def _create(**kwargs):
            defaults = {
                "processo_id": processo.id,
                "status": ExecucaoStatus.AGUARDANDO,
            }
            defaults.update(kwargs)
            e = Execucao(**defaults)
            db.add(e)
            db.commit()
            db.refresh(e)
            return e

        return _create

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    def test_create(self, db, repository, processo):
        execucao = Execucao(
            processo_id=processo.id,
            status=ExecucaoStatus.CRIADO,
        )
        result = repository.create(db, execucao)

        assert result.id is not None
        assert result.processo_id == processo.id
        assert result.status == ExecucaoStatus.CRIADO

    # ------------------------------------------------------------------
    # get_by_id
    # ------------------------------------------------------------------

    def test_get_by_id_encontrado(self, db, repository, execucao_factory):
        e = execucao_factory()
        result = repository.get_by_id(db, e.id)

        assert result is not None
        assert result.id == e.id

    def test_get_by_id_com_relations(self, db, repository, execucao_factory):
        e = execucao_factory()
        result = repository.get_by_id(db, e.id, with_relations=True)

        assert result is not None
        assert result.id == e.id

    def test_get_by_id_nao_encontrado(self, db, repository):
        result = repository.get_by_id(db, uuid4())
        assert result is None

    # ------------------------------------------------------------------
    # get_all_by_processo_id
    # ------------------------------------------------------------------

    def test_get_all_by_processo_id_sem_filtro(
        self, db, repository, execucao_factory, processo
    ):
        execucao_factory()
        execucao_factory()

        result, total = repository.get_all_by_processo_id(db, processo.id)

        assert len(result) == 2
        assert total == 2

    def test_get_all_by_processo_id_com_filtro_status(
        self, db, repository, execucao_factory, processo
    ):
        execucao_factory(status=ExecucaoStatus.AGUARDANDO)
        execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        result, total = repository.get_all_by_processo_id(
            db, processo.id, status=ExecucaoStatus.CONCLUIDO
        )

        assert total == 1
        assert result[0].status == ExecucaoStatus.CONCLUIDO

    def test_get_all_by_processo_id_paginacao(
        self, db, repository, execucao_factory, processo
    ):
        for _ in range(5):
            execucao_factory()

        result, total = repository.get_all_by_processo_id(
            db, processo.id, skip=2, limit=2
        )

        assert total == 5
        assert len(result) == 2

    # ------------------------------------------------------------------
    # get_all
    # ------------------------------------------------------------------

    def test_get_all_sem_filtro(self, db, repository, execucao_factory):
        execucao_factory()
        execucao_factory()

        result, total = repository.get_all(db)

        assert total >= 2

    def test_get_all_com_filtro_status(self, db, repository, execucao_factory):
        execucao_factory(status=ExecucaoStatus.CONCLUIDO)
        execucao_factory(status=ExecucaoStatus.AGUARDANDO)

        result, total = repository.get_all(db, status=ExecucaoStatus.CONCLUIDO)

        assert total >= 1
        for e in result:
            assert e.status == ExecucaoStatus.CONCLUIDO

    def test_get_all_ordem_asc(self, db, repository, execucao_factory):
        execucao_factory()
        execucao_factory()

        result, _ = repository.get_all(db, ordem="asc")
        assert len(result) >= 2

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------

    def test_update(self, db, repository, execucao_factory):
        e = execucao_factory(status=ExecucaoStatus.AGUARDANDO)
        e.status = ExecucaoStatus.EM_EXECUCAO
        updated = repository.update(db, e)

        assert updated.status == ExecucaoStatus.EM_EXECUCAO

    # ------------------------------------------------------------------
    # update_status
    # ------------------------------------------------------------------

    def test_update_status(self, db, repository, execucao_factory):
        e = execucao_factory(status=ExecucaoStatus.AGUARDANDO)
        result = repository.update_status(db, e.id, ExecucaoStatus.EM_EXECUCAO)

        assert result is not None
        assert result.status == ExecucaoStatus.EM_EXECUCAO

    def test_update_status_nao_encontrado(self, db, repository):
        result = repository.update_status(db, uuid4(), ExecucaoStatus.EM_EXECUCAO)
        assert result is None

    # ------------------------------------------------------------------
    # increment_metrics
    # ------------------------------------------------------------------

    def test_increment_metrics(self, db, repository, execucao_factory):
        e = execucao_factory()
        result = repository.increment_metrics(db, e.id, paginas=5, bytes_inc=1024)

        assert result is not None
        assert result.paginas_processadas == 5
        assert result.bytes_extraidos == 1024

    def test_increment_metrics_acumulativo(self, db, repository, execucao_factory):
        e = execucao_factory()
        repository.increment_metrics(db, e.id, paginas=3)
        result = repository.increment_metrics(db, e.id, paginas=2, bytes_inc=500)

        assert result.paginas_processadas == 5
        assert result.bytes_extraidos == 500

    # ------------------------------------------------------------------
    # get_em_execucao
    # ------------------------------------------------------------------

    def test_get_em_execucao_encontrado(
        self, db, repository, execucao_factory, processo
    ):
        e = execucao_factory(status=ExecucaoStatus.EM_EXECUCAO)
        result = repository.get_em_execucao(db, processo.id)

        assert result is not None
        assert result.id == e.id

    def test_get_em_execucao_nao_encontrado(self, db, repository, processo):
        result = repository.get_em_execucao(db, processo.id)
        assert result is None

    def test_get_em_execucao_ignora_outros_status(
        self, db, repository, execucao_factory, processo
    ):
        execucao_factory(status=ExecucaoStatus.AGUARDANDO)
        result = repository.get_em_execucao(db, processo.id)
        assert result is None

    # ------------------------------------------------------------------
    # count_by_status
    # ------------------------------------------------------------------

    def test_count_by_status(self, db, repository, execucao_factory):
        execucao_factory(status=ExecucaoStatus.CONCLUIDO)
        execucao_factory(status=ExecucaoStatus.CONCLUIDO)
        execucao_factory(status=ExecucaoStatus.AGUARDANDO)

        count = repository.count_by_status(db, ExecucaoStatus.CONCLUIDO)
        assert count == 2

    def test_count_by_status_zero(self, db, repository):
        count = repository.count_by_status(db, ExecucaoStatus.FALHOU)
        assert count == 0

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    def test_delete_encontrado(self, db, repository, execucao_factory):
        e = execucao_factory()
        result = repository.delete(db, e.id)

        assert result is True
        assert repository.get_by_id(db, e.id) is None

    def test_delete_nao_encontrado(self, db, repository):
        result = repository.delete(db, uuid4())
        assert result is False
