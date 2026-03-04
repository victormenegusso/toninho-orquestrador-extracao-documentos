"""Testes unitários para PaginaExtraidaService."""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from toninho.core.exceptions import NotFoundError
from toninho.models.enums import ExecucaoStatus, PaginaStatus
from toninho.models.execucao import Execucao
from toninho.models.pagina_extraida import PaginaExtraida
from toninho.models.processo import Processo
from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.pagina_extraida_repository import PaginaExtraidaRepository
from toninho.schemas.pagina_extraida import PaginaExtraidaCreate
from toninho.services.pagina_extraida_service import PaginaExtraidaService


class TestPaginaExtraidaService:
    """Testes para PaginaExtraidaService."""

    @pytest.fixture
    def service(self):
        return PaginaExtraidaService(
            repository=PaginaExtraidaRepository(),
            execucao_repository=ExecucaoRepository(),
        )

    @pytest.fixture
    def processo(self, db):
        p = Processo(nome="Processo Pagina Svc Teste", descricao="desc")
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    @pytest.fixture
    def execucao(self, db, processo):
        e = Execucao(
            processo_id=processo.id,
            status=ExecucaoStatus.EM_EXECUCAO,
            paginas_processadas=0,
            bytes_extraidos=0,
            taxa_erro=0.0,
        )
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
                "url_original": f"https://exemplo.com/pag-{counter['value']}",
                "caminho_arquivo": f"/tmp/pag-{counter['value']}.md",
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

    @pytest.fixture
    def temp_md_file(self):
        """Cria um arquivo markdown temporário para testes de download."""
        fd, path = tempfile.mkstemp(suffix=".md")
        content = b"# Titulo\n\nConteudo da pagina extraida."
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        yield path, content
        if os.path.exists(path):
            os.unlink(path)

    # ------------------------------------------------------------------
    # create_pagina_extraida
    # ------------------------------------------------------------------

    def test_create_pagina_sucesso(self, db, service, execucao):
        pagina_create = PaginaExtraidaCreate(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/pagina",
            caminho_arquivo="/tmp/pagina.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=2048,
        )
        result = service.create_pagina_extraida(db, pagina_create)

        assert result.id is not None
        assert result.execucao_id == execucao.id
        assert result.status == PaginaStatus.SUCESSO

    def test_create_pagina_falhou_sem_erro_mensagem(self, db, service, execucao):
        """schema valida: erro_mensagem obrigatória para FALHOU."""
        with pytest.raises(ValueError, match="erro_mensagem"):
            PaginaExtraidaCreate(
                execucao_id=execucao.id,
                url_original="https://exemplo.com/404",
                caminho_arquivo="/tmp/nenhum.md",
                status=PaginaStatus.FALHOU,
                tamanho_bytes=0,
                # erro_mensagem ausente
            )

    def test_create_pagina_falhou_com_erro_mensagem(self, db, service, execucao):
        pagina_create = PaginaExtraidaCreate(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/404",
            caminho_arquivo="/tmp/nenhum.md",
            status=PaginaStatus.FALHOU,
            tamanho_bytes=0,
            erro_mensagem="HTTP 404: Não encontrado",
        )
        result = service.create_pagina_extraida(db, pagina_create)
        assert result.status == PaginaStatus.FALHOU
        assert result.erro_mensagem == "HTTP 404: Não encontrado"

    def test_create_pagina_atualiza_metricas_execucao(self, db, service, execucao):
        pagina_create = PaginaExtraidaCreate(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/pagina",
            caminho_arquivo="/tmp/pagina.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=2048,
        )
        service.create_pagina_extraida(db, pagina_create)

        db.refresh(execucao)
        assert execucao.paginas_processadas == 1
        assert execucao.bytes_extraidos == 2048

    def test_create_pagina_execucao_inexistente(self, db, service):
        pagina_create = PaginaExtraidaCreate(
            execucao_id=uuid4(),
            url_original="https://exemplo.com",
            caminho_arquivo="/tmp/pagina.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=0,
        )
        with pytest.raises(NotFoundError):
            service.create_pagina_extraida(db, pagina_create)

    # ------------------------------------------------------------------
    # create_pagina_extraida_batch
    # ------------------------------------------------------------------

    def test_create_batch_sucesso(self, db, service, execucao):
        paginas_create = [
            PaginaExtraidaCreate(
                execucao_id=execucao.id,
                url_original=f"https://exemplo.com/pag{i}",
                caminho_arquivo=f"/tmp/pag{i}.md",
                status=PaginaStatus.SUCESSO,
                tamanho_bytes=512,
            )
            for i in range(3)
        ]
        result = service.create_pagina_extraida_batch(db, paginas_create)
        assert len(result) == 3

    def test_create_batch_execucao_inexistente(self, db, service, execucao):
        paginas_create = [
            PaginaExtraidaCreate(
                execucao_id=execucao.id,
                url_original="https://exemplo.com/1",
                caminho_arquivo="/tmp/1.md",
                status=PaginaStatus.SUCESSO,
                tamanho_bytes=0,
            ),
            PaginaExtraidaCreate(
                execucao_id=uuid4(),
                url_original="https://exemplo.com/2",
                caminho_arquivo="/tmp/2.md",
                status=PaginaStatus.SUCESSO,
                tamanho_bytes=0,
            ),
        ]
        with pytest.raises(NotFoundError):
            service.create_pagina_extraida_batch(db, paginas_create)

    # ------------------------------------------------------------------
    # get_pagina_extraida
    # ------------------------------------------------------------------

    def test_get_pagina_sucesso(self, db, service, pagina_factory):
        pagina = pagina_factory()
        result = service.get_pagina_extraida(db, pagina.id)
        assert result.id == pagina.id
        assert result.download_url == f"/api/v1/paginas/{pagina.id}/download"

    def test_get_pagina_nao_encontrada(self, db, service):
        with pytest.raises(NotFoundError):
            service.get_pagina_extraida(db, uuid4())

    # ------------------------------------------------------------------
    # list_paginas_by_execucao
    # ------------------------------------------------------------------

    def test_list_paginas_sem_filtro(self, db, service, pagina_factory, execucao):
        pagina_factory()
        pagina_factory()

        result = service.list_paginas_by_execucao(db, execucao.id)
        assert result.meta.total == 2
        assert len(result.data) == 2

    def test_list_paginas_com_filtro_status(
        self, db, service, pagina_factory, execucao
    ):
        pagina_factory(status=PaginaStatus.SUCESSO)
        pagina_factory(status=PaginaStatus.FALHOU, erro_mensagem="Erro")

        result = service.list_paginas_by_execucao(
            db, execucao.id, status=PaginaStatus.SUCESSO
        )
        assert result.meta.total == 1

    def test_list_paginas_paginacao(self, db, service, pagina_factory, execucao):
        for _ in range(5):
            pagina_factory()

        result = service.list_paginas_by_execucao(db, execucao.id, page=2, per_page=3)
        assert result.meta.total == 5
        assert result.meta.page == 2

    def test_list_paginas_execucao_inexistente(self, db, service):
        with pytest.raises(NotFoundError):
            service.list_paginas_by_execucao(db, uuid4())

    # ------------------------------------------------------------------
    # get_estatisticas_paginas
    # ------------------------------------------------------------------

    def test_get_estatisticas_paginas(self, db, service, pagina_factory, execucao):
        pagina_factory(status=PaginaStatus.SUCESSO, tamanho_bytes=1000)
        pagina_factory(status=PaginaStatus.SUCESSO, tamanho_bytes=2000)
        pagina_factory(
            status=PaginaStatus.FALHOU, erro_mensagem="Erro", tamanho_bytes=0
        )
        pagina_factory(status=PaginaStatus.IGNORADO, tamanho_bytes=0)

        result = service.get_estatisticas_paginas(db, execucao.id)

        assert result.execucao_id == execucao.id
        assert result.total == 4
        assert result.sucesso == 2
        assert result.falhou == 1
        assert result.ignorado == 1
        assert result.taxa_sucesso == 50.0
        assert result.tamanho_total_bytes == 3000
        assert result.tamanho_medio_bytes == 750.0
        assert result.maior_pagina_bytes == 2000
        assert result.menor_pagina_bytes == 0

    def test_get_estatisticas_paginas_sem_paginas(self, db, service, execucao):
        result = service.get_estatisticas_paginas(db, execucao.id)

        assert result.total == 0
        assert result.taxa_sucesso == 0.0
        assert result.tamanho_total_bytes == 0
        assert result.tamanho_medio_bytes == 0.0

    def test_get_estatisticas_execucao_inexistente(self, db, service):
        with pytest.raises(NotFoundError):
            service.get_estatisticas_paginas(db, uuid4())

    # ------------------------------------------------------------------
    # download_pagina
    # ------------------------------------------------------------------

    def test_download_pagina_sucesso(self, db, service, execucao, temp_md_file):
        filepath, expected_content = temp_md_file
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/pagina",
            caminho_arquivo=filepath,
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=len(expected_content),
        )
        db.add(pagina)
        db.commit()
        db.refresh(pagina)

        conteudo, content_type, filename = service.download_pagina(db, pagina.id)

        assert conteudo == expected_content
        assert content_type == "text/markdown"
        assert filename.endswith(".md")

    def test_download_pagina_arquivo_nao_existe(self, db, service, execucao):
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/pagina",
            caminho_arquivo="/tmp/arquivo_inexistente_abc123.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=0,
        )
        db.add(pagina)
        db.commit()
        db.refresh(pagina)

        with pytest.raises(FileNotFoundError):
            service.download_pagina(db, pagina.id)

    def test_download_pagina_nao_encontrada(self, db, service):
        with pytest.raises(NotFoundError):
            service.download_pagina(db, uuid4())

    # ------------------------------------------------------------------
    # delete_pagina
    # ------------------------------------------------------------------

    def test_delete_pagina_sem_arquivo(self, db, service, pagina_factory):
        pagina = pagina_factory(caminho_arquivo="/tmp/nao_existe_xyz.md")
        result = service.delete_pagina(db, pagina.id)
        assert result is True

        with pytest.raises(NotFoundError):
            service.get_pagina_extraida(db, pagina.id)

    def test_delete_pagina_com_arquivo(self, db, service, execucao):
        # Criar arquivo temporário
        fd, path = tempfile.mkstemp(suffix=".md")
        os.write(fd, b"# Conteudo")
        os.close(fd)
        assert Path(path).exists()

        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/pagina",
            caminho_arquivo=path,
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=10,
        )
        db.add(pagina)
        db.commit()
        db.refresh(pagina)

        service.delete_pagina(db, pagina.id)

        assert not Path(path).exists()

    def test_delete_pagina_nao_encontrada(self, db, service):
        with pytest.raises(NotFoundError):
            service.delete_pagina(db, uuid4())
