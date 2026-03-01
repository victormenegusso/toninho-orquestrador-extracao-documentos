"""Testes unitários para PaginaExtraidaRepository."""

import pytest
from uuid import uuid4

from toninho.models.enums import ExecucaoStatus, PaginaStatus
from toninho.models.execucao import Execucao
from toninho.models.pagina_extraida import PaginaExtraida
from toninho.models.processo import Processo
from toninho.repositories.pagina_extraida_repository import PaginaExtraidaRepository


class TestPaginaExtraidaRepository:
    """Testes para PaginaExtraidaRepository."""

    @pytest.fixture
    def repository(self):
        return PaginaExtraidaRepository()

    @pytest.fixture
    def processo(self, db):
        p = Processo(nome="Processo Pagina Repo Teste", descricao="desc")
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
    def pagina_factory(self, db, execucao):
        counter = {"value": 0}

        def _create(**kwargs):
            counter["value"] += 1
            defaults = {
                "execucao_id": execucao.id,
                "url_original": f"https://exemplo.com/pagina-{counter['value']}",
                "caminho_arquivo": f"/tmp/pagina-{counter['value']}.md",
                "status": PaginaStatus.SUCESSO,
                "tamanho_bytes": 1024,
            }
            defaults.update(kwargs)
            p = PaginaExtraida(**defaults)
            db.add(p)
            db.commit()
            db.refresh(p)
            return p

        return _create

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    def test_create(self, db, repository, execucao):
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com",
            caminho_arquivo="/tmp/pagina.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=512,
        )
        result = repository.create(db, pagina)

        assert result.id is not None
        assert result.execucao_id == execucao.id
        assert result.status == PaginaStatus.SUCESSO

    def test_create_com_erro(self, db, repository, execucao):
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/404",
            caminho_arquivo="/tmp/nenhum.md",
            status=PaginaStatus.FALHOU,
            tamanho_bytes=0,
            erro_mensagem="HTTP 404: Página não encontrada",
        )
        result = repository.create(db, pagina)

        assert result.status == PaginaStatus.FALHOU
        assert result.erro_mensagem == "HTTP 404: Página não encontrada"

    # ------------------------------------------------------------------
    # create_batch
    # ------------------------------------------------------------------

    def test_create_batch(self, db, repository, execucao):
        paginas = [
            PaginaExtraida(
                execucao_id=execucao.id,
                url_original=f"https://exemplo.com/pag{i}",
                caminho_arquivo=f"/tmp/pag{i}.md",
                status=PaginaStatus.SUCESSO,
                tamanho_bytes=512,
            )
            for i in range(3)
        ]
        result = repository.create_batch(db, paginas)
        assert len(result) == 3
        for p in result:
            assert p.id is not None

    # ------------------------------------------------------------------
    # get_by_id
    # ------------------------------------------------------------------

    def test_get_by_id_encontrado(self, db, repository, pagina_factory):
        pagina = pagina_factory()
        result = repository.get_by_id(db, pagina.id)
        assert result is not None
        assert result.id == pagina.id

    def test_get_by_id_nao_encontrado(self, db, repository):
        result = repository.get_by_id(db, uuid4())
        assert result is None

    # ------------------------------------------------------------------
    # get_by_execucao_id
    # ------------------------------------------------------------------

    def test_get_by_execucao_id_sem_filtro(self, db, repository, pagina_factory, execucao):
        pagina_factory()
        pagina_factory()

        result, total = repository.get_by_execucao_id(db, execucao.id)
        assert total == 2
        assert len(result) == 2

    def test_get_by_execucao_id_com_filtro_status(self, db, repository, pagina_factory, execucao):
        pagina_factory(status=PaginaStatus.SUCESSO)
        pagina_factory(status=PaginaStatus.FALHOU, erro_mensagem="Erro 404")

        result, total = repository.get_by_execucao_id(
            db, execucao.id, status=PaginaStatus.SUCESSO
        )
        assert total == 1
        assert result[0].status == PaginaStatus.SUCESSO

    def test_get_by_execucao_id_paginacao(self, db, repository, pagina_factory, execucao):
        for _ in range(5):
            pagina_factory()

        result, total = repository.get_by_execucao_id(db, execucao.id, skip=0, limit=3)
        assert total == 5
        assert len(result) == 3

    # ------------------------------------------------------------------
    # get_by_url
    # ------------------------------------------------------------------

    def test_get_by_url_encontrado(self, db, repository, pagina_factory, execucao):
        pagina_factory(url_original="https://exemplo.com/especifica")
        result = repository.get_by_url(db, execucao.id, "https://exemplo.com/especifica")

        assert result is not None
        assert result.url_original == "https://exemplo.com/especifica"

    def test_get_by_url_nao_encontrado(self, db, repository, execucao):
        result = repository.get_by_url(db, execucao.id, "https://inexistente.com")
        assert result is None

    # ------------------------------------------------------------------
    # count_by_status
    # ------------------------------------------------------------------

    def test_count_by_status(self, db, repository, pagina_factory, execucao):
        pagina_factory(status=PaginaStatus.SUCESSO)
        pagina_factory(status=PaginaStatus.SUCESSO)
        pagina_factory(status=PaginaStatus.FALHOU, erro_mensagem="Erro")
        pagina_factory(status=PaginaStatus.IGNORADO)

        result = repository.count_by_status(db, execucao.id)

        assert result[PaginaStatus.SUCESSO] == 2
        assert result[PaginaStatus.FALHOU] == 1
        assert result[PaginaStatus.IGNORADO] == 1

    def test_count_by_status_sem_paginas(self, db, repository, execucao):
        result = repository.count_by_status(db, execucao.id)
        assert all(v == 0 for v in result.values())

    # ------------------------------------------------------------------
    # sum_tamanho_bytes
    # ------------------------------------------------------------------

    def test_sum_tamanho_bytes(self, db, repository, pagina_factory, execucao):
        pagina_factory(tamanho_bytes=1000)
        pagina_factory(tamanho_bytes=2000)
        pagina_factory(tamanho_bytes=500)

        result = repository.sum_tamanho_bytes(db, execucao.id)
        assert result == 3500

    def test_sum_tamanho_bytes_sem_paginas(self, db, repository, execucao):
        result = repository.sum_tamanho_bytes(db, execucao.id)
        assert result == 0

    # ------------------------------------------------------------------
    # delete_by_execucao_id
    # ------------------------------------------------------------------

    def test_delete_by_execucao_id(self, db, repository, pagina_factory, execucao):
        pagina_factory()
        pagina_factory()

        count = repository.delete_by_execucao_id(db, execucao.id)
        assert count == 2

        _, total = repository.get_by_execucao_id(db, execucao.id)
        assert total == 0

    def test_delete_by_execucao_id_sem_paginas(self, db, repository, execucao):
        count = repository.delete_by_execucao_id(db, execucao.id)
        assert count == 0
