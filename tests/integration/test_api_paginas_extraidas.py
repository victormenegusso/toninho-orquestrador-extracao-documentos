"""Testes de integração para API de Páginas Extraídas."""

import os
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(test_engine):
    """Cliente de teste com override do banco de dados."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
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
def processo(db):
    p = Processo(nome="Processo Pagina API Teste", descricao="desc")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def execucao(db, processo):
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
def pagina_factory(db, execucao):
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
def temp_md_file():
    """Cria arquivo markdown temporário."""
    fd, path = tempfile.mkstemp(suffix=".md")
    content = b"# Titulo\n\nConteudo da pagina extraida."
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    yield path, content
    if os.path.exists(path):
        os.unlink(path)


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestPaginasExtraidasAPI:

    # ------------------------------------------------------------------
    # POST /api/v1/paginas
    # ------------------------------------------------------------------

    def test_create_pagina_sucesso(self, client, execucao):
        payload = {
            "execucao_id": str(execucao.id),
            "url_original": "https://exemplo.com/pagina",
            "caminho_arquivo": "/tmp/pagina.md",
            "status": "sucesso",
            "tamanho_bytes": 2048,
        }
        response = client.post("/api/v1/paginas", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "sucesso"
        assert data["data"]["tamanho_bytes"] == 2048

    def test_create_pagina_falhou_com_mensagem(self, client, execucao):
        payload = {
            "execucao_id": str(execucao.id),
            "url_original": "https://exemplo.com/404",
            "caminho_arquivo": "/tmp/nenhum.md",
            "status": "falhou",
            "tamanho_bytes": 0,
            "erro_mensagem": "HTTP 404: Página não encontrada",
        }
        response = client.post("/api/v1/paginas", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["status"] == "falhou"

    def test_create_pagina_falhou_sem_mensagem(self, client, execucao):
        payload = {
            "execucao_id": str(execucao.id),
            "url_original": "https://exemplo.com/404",
            "caminho_arquivo": "/tmp/nenhum.md",
            "status": "falhou",
            "tamanho_bytes": 0,
        }
        response = client.post("/api/v1/paginas", json=payload)
        assert response.status_code == 422  # pydantic validation error

    def test_create_pagina_execucao_inexistente(self, client):
        payload = {
            "execucao_id": str(uuid4()),
            "url_original": "https://exemplo.com",
            "caminho_arquivo": "/tmp/pagina.md",
            "status": "sucesso",
            "tamanho_bytes": 0,
        }
        response = client.post("/api/v1/paginas", json=payload)
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # POST /api/v1/paginas/batch
    # ------------------------------------------------------------------

    def test_create_paginas_batch_sucesso(self, client, execucao):
        payload = [
            {
                "execucao_id": str(execucao.id),
                "url_original": f"https://exemplo.com/pag{i}",
                "caminho_arquivo": f"/tmp/pag{i}.md",
                "status": "sucesso",
                "tamanho_bytes": 512,
            }
            for i in range(3)
        ]
        response = client.post("/api/v1/paginas/batch", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert len(data["data"]) == 3

    def test_create_paginas_batch_execucao_inexistente(self, client, execucao):
        payload = [
            {
                "execucao_id": str(execucao.id),
                "url_original": "https://exemplo.com/1",
                "caminho_arquivo": "/tmp/1.md",
                "status": "sucesso",
                "tamanho_bytes": 0,
            },
            {
                "execucao_id": str(uuid4()),
                "url_original": "https://exemplo.com/2",
                "caminho_arquivo": "/tmp/2.md",
                "status": "sucesso",
                "tamanho_bytes": 0,
            },
        ]
        response = client.post("/api/v1/paginas/batch", json=payload)
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/execucoes/{id}/paginas
    # ------------------------------------------------------------------

    def test_list_paginas_sucesso(self, client, pagina_factory, execucao):
        pagina_factory()
        pagina_factory()

        response = client.get(f"/api/v1/execucoes/{execucao.id}/paginas")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 2

    def test_list_paginas_filtro_status(self, client, pagina_factory, execucao):
        pagina_factory(status=PaginaStatus.SUCESSO)
        pagina_factory(
            status=PaginaStatus.FALHOU,
            erro_mensagem="Erro 404",
        )

        response = client.get(
            f"/api/v1/execucoes/{execucao.id}/paginas?status=sucesso"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 1
        assert data["data"][0]["status"] == "sucesso"

    def test_list_paginas_paginacao(self, client, pagina_factory, execucao):
        for _ in range(5):
            pagina_factory()

        response = client.get(
            f"/api/v1/execucoes/{execucao.id}/paginas?page=1&per_page=3"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 5
        assert len(data["data"]) == 3

    def test_list_paginas_execucao_inexistente(self, client):
        response = client.get(f"/api/v1/execucoes/{uuid4()}/paginas")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/execucoes/{id}/paginas/estatisticas
    # ------------------------------------------------------------------

    def test_get_estatisticas_paginas(self, client, pagina_factory, execucao):
        pagina_factory(status=PaginaStatus.SUCESSO, tamanho_bytes=1000)
        pagina_factory(
            status=PaginaStatus.FALHOU,
            erro_mensagem="Erro",
            tamanho_bytes=0,
        )

        response = client.get(
            f"/api/v1/execucoes/{execucao.id}/paginas/estatisticas"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 2
        assert data["data"]["sucesso"] == 1
        assert data["data"]["falhou"] == 1
        assert data["data"]["taxa_sucesso"] == 50.0

    def test_get_estatisticas_execucao_inexistente(self, client):
        response = client.get(
            f"/api/v1/execucoes/{uuid4()}/paginas/estatisticas"
        )
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/paginas/{id}
    # ------------------------------------------------------------------

    def test_get_pagina_sucesso(self, client, pagina_factory):
        pagina = pagina_factory()
        response = client.get(f"/api/v1/paginas/{pagina.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(pagina.id)
        assert "download_url" in data["data"]

    def test_get_pagina_nao_encontrada(self, client):
        response = client.get(f"/api/v1/paginas/{uuid4()}")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/paginas/{id}/download
    # ------------------------------------------------------------------

    def test_download_pagina_sucesso(self, client, db, execucao, temp_md_file):
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

        response = client.get(f"/api/v1/paginas/{pagina.id}/download")
        assert response.status_code == 200
        assert response.content == expected_content
        assert "content-disposition" in response.headers

    def test_download_pagina_arquivo_nao_existe(self, client, pagina_factory):
        pagina = pagina_factory(caminho_arquivo="/tmp/arquivo_inexistente_xyz123.md")
        response = client.get(f"/api/v1/paginas/{pagina.id}/download")
        assert response.status_code == 404

    def test_download_pagina_nao_encontrada(self, client):
        response = client.get(f"/api/v1/paginas/{uuid4()}/download")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # DELETE /api/v1/paginas/{id}
    # ------------------------------------------------------------------

    def test_delete_pagina_sucesso(self, client, pagina_factory):
        pagina = pagina_factory()
        response = client.delete(f"/api/v1/paginas/{pagina.id}")
        assert response.status_code == 204

        # Verificar que foi deletado
        response = client.get(f"/api/v1/paginas/{pagina.id}")
        assert response.status_code == 404

    def test_delete_pagina_com_arquivo(self, client, db, execucao):
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

        response = client.delete(f"/api/v1/paginas/{pagina.id}")
        assert response.status_code == 204
        assert not Path(path).exists()

    def test_delete_pagina_nao_encontrada(self, client):
        response = client.delete(f"/api/v1/paginas/{uuid4()}")
        assert response.status_code == 404

    def test_headers_download(self, client, db, execucao, temp_md_file):
        filepath, content = temp_md_file
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/pagina",
            caminho_arquivo=filepath,
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=len(content),
        )
        db.add(pagina)
        db.commit()
        db.refresh(pagina)

        response = client.get(f"/api/v1/paginas/{pagina.id}/download")
        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")
