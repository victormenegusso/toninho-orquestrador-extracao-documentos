"""
Testes de integração para Detalhes e Downloads (PRD-017).

Testa as rotas HTML de páginas extraídas, preview modal, downloads individuais
e em lote (ZIP), busca e filtros.
"""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.enums import ExecucaoStatus, PaginaStatus
from toninho.models.execucao import Execucao
from toninho.models.pagina_extraida import PaginaExtraida
from toninho.models.processo import Processo


@pytest.fixture
def client(test_engine):
    """Fixture que retorna cliente de teste com banco de dados de teste."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=True)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def processo_no_db(db):
    """Cria processo de base para testes."""
    processo = Processo(
        nome="Processo Downloads Test",
        descricao="Processo criado para testes de downloads",
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)
    return processo


@pytest.fixture
def execucao_no_db(db, processo_no_db):
    """Cria execução concluída no banco de dados para testes."""
    execucao = Execucao(
        processo_id=processo_no_db.id,
        status=ExecucaoStatus.CONCLUIDO,
        paginas_processadas=3,
        bytes_extraidos=3072,
        taxa_erro=0.0,
        tentativa_atual=1,
    )
    db.add(execucao)
    db.commit()
    db.refresh(execucao)
    return execucao


@pytest.fixture
def pagina_sucesso_no_db(db, execucao_no_db):
    """Cria uma pagina com sucesso no banco de dados, com arquivo temporario."""
    # Create a real temp file for download tests
    tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w")
    tmp.write("# Test Content\n\nConteúdo de teste para dowload.\n")
    tmp.flush()
    tmp.close()
    filepath = tmp.name

    pagina = PaginaExtraida(
        execucao_id=execucao_no_db.id,
        url_original="https://exemplo.com/pagina-sucesso",
        caminho_arquivo=filepath,
        status=PaginaStatus.SUCESSO,
        tamanho_bytes=len("# Test Content\n\nConteúdo de teste para dowload.\n"),
    )
    db.add(pagina)
    db.commit()
    db.refresh(pagina)
    yield pagina
    # Cleanup temp file
    Path(filepath).unlink(missing_ok=True)


@pytest.fixture
def pagina_falhou_no_db(db, execucao_no_db):
    """Cria uma pagina com falha no banco de dados."""
    pagina = PaginaExtraida(
        execucao_id=execucao_no_db.id,
        url_original="https://exemplo.com/pagina-erro",
        caminho_arquivo="/tmp/nao-existe.md",
        status=PaginaStatus.FALHOU,
        tamanho_bytes=0,
        erro_mensagem="Timeout ao acessar a URL",
    )
    db.add(pagina)
    db.commit()
    db.refresh(pagina)
    return pagina


# ===========================================================================
# Testes: GET /execucoes/{id}/paginas
# ===========================================================================


class TestExecucaoPaginasPage:
    """Testa a página de listagem de páginas de uma execução."""

    def test_execucao_paginas_retorna_200(self, client, execucao_no_db):
        """GET /execucoes/{id}/paginas retorna 200."""
        resp = client.get(f"/execucoes/{execucao_no_db.id}/paginas")
        assert resp.status_code == 200

    def test_execucao_paginas_contem_html(self, client, execucao_no_db):
        """Resposta é HTML com estrutura esperada."""
        resp = client.get(f"/execucoes/{execucao_no_db.id}/paginas")
        assert "text/html" in resp.headers["content-type"]
        assert (
            b"P\xc3\xa1ginas Extra\xc3\xaddas" in resp.content
        )  # "Páginas Extraídas" in UTF-8

    def test_execucao_paginas_link_voltar(self, client, execucao_no_db):
        """Página contém link de volta para a execução."""
        resp = client.get(f"/execucoes/{execucao_no_db.id}/paginas")
        assert str(execucao_no_db.id).encode() in resp.content

    def test_execucao_paginas_botao_download_all(self, client, execucao_no_db):
        """Página contém botão de download ZIP."""
        resp = client.get(f"/execucoes/{execucao_no_db.id}/paginas")
        assert b"download-all" in resp.content or b"Baixar Todas" in resp.content

    def test_execucao_paginas_exibe_paginas(
        self, client, execucao_no_db, pagina_sucesso_no_db
    ):
        """Página exibe páginas existentes."""
        resp = client.get(f"/execucoes/{execucao_no_db.id}/paginas")
        assert resp.status_code == 200
        assert b"exemplo.com" in resp.content

    def test_execucao_paginas_filtro_status(
        self, client, execucao_no_db, pagina_sucesso_no_db, pagina_falhou_no_db
    ):
        """Filtro por status funciona."""
        resp = client.get(f"/execucoes/{execucao_no_db.id}/paginas?status=sucesso")
        assert resp.status_code == 200
        # Deve conter a página de sucesso
        assert b"sucesso" in resp.content

    def test_execucao_paginas_nao_encontrada_retorna_404(self, client):
        """Execução inexistente retorna 404."""
        resp = client.get(f"/execucoes/{uuid4()}/paginas")
        assert resp.status_code == 404

    def test_execucao_paginas_sem_paginas_mostra_vazio(self, client, execucao_no_db):
        """Página sem páginas exibe mensagem de vazio ou estrutura de página."""
        resp = client.get(f"/execucoes/{execucao_no_db.id}/paginas")
        assert resp.status_code == 200
        assert b"P\xc3\xa1ginas Extra" in resp.content  # "Páginas Extra" in page


# ===========================================================================
# Testes: GET /paginas/search
# ===========================================================================


class TestPaginasSearch:
    """Testa o partial de busca de páginas."""

    def test_paginas_search_retorna_200(self, client, execucao_no_db):
        """GET /paginas/search retorna 200."""
        resp = client.get(f"/paginas/search?execucao_id={execucao_no_db.id}")
        assert resp.status_code == 200

    def test_paginas_search_contem_html(self, client, execucao_no_db):
        """Resposta é HTML."""
        resp = client.get(f"/paginas/search?execucao_id={execucao_no_db.id}")
        assert "text/html" in resp.headers["content-type"]

    def test_paginas_search_com_paginas(
        self, client, execucao_no_db, pagina_sucesso_no_db
    ):
        """Busca retorna páginas existentes."""
        resp = client.get(f"/paginas/search?execucao_id={execucao_no_db.id}")
        assert resp.status_code == 200
        assert b"exemplo.com" in resp.content

    def test_paginas_search_filtro_status_sucesso(
        self, client, execucao_no_db, pagina_sucesso_no_db, pagina_falhou_no_db
    ):
        """Filtro por status=sucesso retorna apenas páginas com sucesso."""
        resp = client.get(
            f"/paginas/search?execucao_id={execucao_no_db.id}&status=sucesso"
        )
        assert resp.status_code == 200
        assert b"pagina-sucesso" in resp.content

    def test_paginas_search_filtro_status_falhou(
        self, client, execucao_no_db, pagina_sucesso_no_db, pagina_falhou_no_db
    ):
        """Filtro por status=falhou retorna apenas páginas falhas."""
        resp = client.get(
            f"/paginas/search?execucao_id={execucao_no_db.id}&status=falhou"
        )
        assert resp.status_code == 200
        assert b"pagina-erro" in resp.content

    def test_paginas_search_sem_resultados(self, client, execucao_no_db):
        """Busca sem resultados mostra mensagem vazia."""
        resp = client.get(f"/paginas/search?execucao_id={execucao_no_db.id}")
        assert resp.status_code == 200
        # Empty state should be shown (partial HTML, no <html> tag)
        assert b"Nenhuma p" in resp.content or b"Ajuste" in resp.content


# ===========================================================================
# Testes: GET /paginas/{id}
# ===========================================================================


class TestPaginaDetailPage:
    """Testa a página de detalhes de uma página extraída."""

    def test_pagina_detail_retorna_200(self, client, pagina_sucesso_no_db):
        """GET /paginas/{id} retorna 200."""
        resp = client.get(f"/paginas/{pagina_sucesso_no_db.id}")
        assert resp.status_code == 200

    def test_pagina_detail_contem_html(self, client, pagina_sucesso_no_db):
        """Resposta é HTML."""
        resp = client.get(f"/paginas/{pagina_sucesso_no_db.id}")
        assert "text/html" in resp.headers["content-type"]

    def test_pagina_detail_exibe_url(self, client, pagina_sucesso_no_db):
        """Página exibe URL original da página."""
        resp = client.get(f"/paginas/{pagina_sucesso_no_db.id}")
        assert b"exemplo.com/pagina-sucesso" in resp.content

    def test_pagina_detail_exibe_status(self, client, pagina_sucesso_no_db):
        """Página exibe status da extração."""
        resp = client.get(f"/paginas/{pagina_sucesso_no_db.id}")
        assert b"sucesso" in resp.content

    def test_pagina_detail_sucesso_exibe_download(self, client, pagina_sucesso_no_db):
        """Página de sucesso exibe link de download."""
        resp = client.get(f"/paginas/{pagina_sucesso_no_db.id}")
        assert b"download" in resp.content.lower()

    def test_pagina_detail_falhou_exibe_erro(self, client, pagina_falhou_no_db):
        """Página falha exibe mensagem de erro."""
        resp = client.get(f"/paginas/{pagina_falhou_no_db.id}")
        assert resp.status_code == 200
        assert b"falhou" in resp.content

    def test_pagina_detail_nao_encontrada_retorna_404(self, client):
        """Página inexistente retorna 404."""
        resp = client.get(f"/paginas/{uuid4()}")
        assert resp.status_code == 404


# ===========================================================================
# Testes: GET /api/v1/execucoes/{id}/download-all
# ===========================================================================


class TestDownloadAllEndpoint:
    """Testa o endpoint de download ZIP de páginas."""

    def test_download_all_sem_paginas_retorna_404(self, client, execucao_no_db):
        """Execução sem páginas com sucesso retorna 404."""
        resp = client.get(f"/api/v1/execucoes/{execucao_no_db.id}/download-all")
        assert resp.status_code == 404

    def test_download_all_execucao_inexistente_retorna_404(self, client):
        """Execução inexistente retorna 404."""
        resp = client.get(f"/api/v1/execucoes/{uuid4()}/download-all")
        assert resp.status_code == 404

    def test_download_all_com_paginas_retorna_200(
        self, client, execucao_no_db, pagina_sucesso_no_db
    ):
        """Execução com páginas com sucesso retorna 200 com ZIP."""
        resp = client.get(f"/api/v1/execucoes/{execucao_no_db.id}/download-all")
        assert resp.status_code == 200

    def test_download_all_content_type_zip(
        self, client, execucao_no_db, pagina_sucesso_no_db
    ):
        """Response tem content-type application/zip."""
        resp = client.get(f"/api/v1/execucoes/{execucao_no_db.id}/download-all")
        assert resp.status_code == 200
        assert "application/zip" in resp.headers["content-type"]

    def test_download_all_header_disposition(
        self, client, execucao_no_db, pagina_sucesso_no_db
    ):
        """Response tem header Content-Disposition com filename."""
        resp = client.get(f"/api/v1/execucoes/{execucao_no_db.id}/download-all")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert ".zip" in resp.headers.get("content-disposition", "")

    def test_download_all_apenas_paginas_falha_retorna_404(
        self, client, execucao_no_db, pagina_falhou_no_db
    ):
        """Execução com apenas páginas falhas retorna 404 (ZIP vazio não permitido)."""
        resp = client.get(f"/api/v1/execucoes/{execucao_no_db.id}/download-all")
        assert resp.status_code == 404

    def test_download_all_conteudo_e_zip_valido(
        self, client, execucao_no_db, pagina_sucesso_no_db
    ):
        """Resposta ZIP é um arquivo ZIP válido."""
        import io
        import zipfile

        resp = client.get(f"/api/v1/execucoes/{execucao_no_db.id}/download-all")
        assert resp.status_code == 200
        # ZIP should be parseable
        buf = io.BytesIO(resp.content)
        zf = zipfile.ZipFile(buf)
        assert zf is not None
        zf.close()


# ===========================================================================
# Testes: GET /api/v1/paginas/{id}/content
# ===========================================================================


class TestPaginaContentEndpoint:
    """Testa o endpoint de conteúdo de página (preview)."""

    def test_content_retorna_200(self, client, pagina_sucesso_no_db):
        """GET /api/v1/paginas/{id}/content retorna 200."""
        resp = client.get(f"/api/v1/paginas/{pagina_sucesso_no_db.id}/content")
        assert resp.status_code == 200

    def test_content_retorna_texto(self, client, pagina_sucesso_no_db):
        """Endpoint retorna conteúdo como texto."""
        resp = client.get(f"/api/v1/paginas/{pagina_sucesso_no_db.id}/content")
        assert "text/plain" in resp.headers["content-type"]
        assert b"Test Content" in resp.content

    def test_content_pagina_inexistente_retorna_404(self, client):
        """Página inexistente retorna 404."""
        resp = client.get(f"/api/v1/paginas/{uuid4()}/content")
        assert resp.status_code == 404

    def test_content_arquivo_inexistente_retorna_404(self, client, pagina_falhou_no_db):
        """Página com arquivo inexistente retorna 404."""
        resp = client.get(f"/api/v1/paginas/{pagina_falhou_no_db.id}/content")
        assert resp.status_code == 404


# ===========================================================================
# Testes: GET /api/v1/paginas/{id}/download (já existente)
# ===========================================================================


class TestDownloadIndividualEndpoint:
    """Testa o endpoint de download individual de arquivo markdown."""

    def test_download_pagina_sucesso(self, client, pagina_sucesso_no_db):
        """Download de página com arquivo existente retorna 200."""
        resp = client.get(f"/api/v1/paginas/{pagina_sucesso_no_db.id}/download")
        assert resp.status_code == 200

    def test_download_pagina_content_type(self, client, pagina_sucesso_no_db):
        """Download retorna content-type text/markdown."""
        resp = client.get(f"/api/v1/paginas/{pagina_sucesso_no_db.id}/download")
        assert resp.status_code == 200
        assert (
            "markdown" in resp.headers["content-type"]
            or "text" in resp.headers["content-type"]
        )

    def test_download_pagina_inexistente_retorna_404(self, client):
        """Página inexistente retorna 404."""
        resp = client.get(f"/api/v1/paginas/{uuid4()}/download")
        assert resp.status_code == 404

    def test_download_pagina_arquivo_inexistente_retorna_404(
        self, client, pagina_falhou_no_db
    ):
        """Página com arquivo inexistente retorna 404."""
        resp = client.get(f"/api/v1/paginas/{pagina_falhou_no_db.id}/download")
        assert resp.status_code == 404
