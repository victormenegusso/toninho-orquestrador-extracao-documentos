"""Testes de integração para API de Execuções."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.enums import ExecucaoStatus
from toninho.models.execucao import Execucao
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
    p = Processo(nome="Processo Exec Teste", descricao="desc")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def execucao_factory(db, processo):
    """Factory para criar execuções diretamente no DB."""
    counter = {"value": 0}

    def _create(**kwargs):
        counter["value"] += 1
        defaults = {
            "processo_id": processo.id,
            "status": ExecucaoStatus.AGUARDANDO,
        }
        defaults.update(kwargs)
        exec_ = Execucao(**defaults)
        db.add(exec_)
        db.commit()
        db.refresh(exec_)
        return exec_

    return _create


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestExecucaoAPI:
    # ------------------------------------------------------------------
    # POST /processos/{id}/execucoes
    # ------------------------------------------------------------------

    def test_create_sucesso(self, client, processo):
        response = client.post(f"/api/v1/processos/{processo.id}/execucoes")

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["processo_id"] == str(processo.id)
        assert data["data"]["status"] in (
            ExecucaoStatus.AGUARDANDO.value,
            ExecucaoStatus.CRIADO.value,
        )

    def test_create_processo_nao_existe(self, client):
        response = client.post(f"/api/v1/processos/{uuid4()}/execucoes")
        assert response.status_code == 404

    def test_create_bloqueia_se_em_execucao(self, client, processo, execucao_factory):
        """Não deve permitir segunda execução com status EM_EXECUCAO."""
        execucao_factory(status=ExecucaoStatus.EM_EXECUCAO)

        response = client.post(f"/api/v1/processos/{processo.id}/execucoes")
        assert response.status_code == 409

    # ------------------------------------------------------------------
    # GET /processos/{id}/execucoes
    # ------------------------------------------------------------------

    def test_list_execucoes_por_processo(self, client, processo, execucao_factory):
        execucao_factory()
        execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        response = client.get(f"/api/v1/processos/{processo.id}/execucoes")

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] >= 2

    def test_list_execucoes_filtro_status(self, client, processo, execucao_factory):
        execucao_factory(status=ExecucaoStatus.AGUARDANDO)
        execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        response = client.get(
            f"/api/v1/processos/{processo.id}/execucoes?status=concluido"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] >= 1
        for item in data["data"]:
            assert item["status"] == "concluido"

    # ------------------------------------------------------------------
    # GET /execucoes (global)
    # ------------------------------------------------------------------

    def test_list_execucoes_global(self, client, execucao_factory):
        execucao_factory()
        execucao_factory()

        response = client.get("/api/v1/execucoes")

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] >= 2

    def test_list_execucoes_paginacao(self, client, execucao_factory):
        for _ in range(5):
            execucao_factory()

        response = client.get("/api/v1/execucoes?page=1&per_page=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 3
        assert data["meta"]["per_page"] == 3

    # ------------------------------------------------------------------
    # GET /execucoes/{id}
    # ------------------------------------------------------------------

    def test_get_execucao(self, client, execucao_factory):
        exec_ = execucao_factory()

        response = client.get(f"/api/v1/execucoes/{exec_.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(exec_.id)

    def test_get_execucao_nao_existe(self, client):
        response = client.get(f"/api/v1/execucoes/{uuid4()}")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /execucoes/{id}/detalhes
    # ------------------------------------------------------------------

    def test_get_execucao_detalhes(self, client, execucao_factory):
        exec_ = execucao_factory()

        response = client.get(f"/api/v1/execucoes/{exec_.id}/detalhes")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(exec_.id)
        assert "metricas" in data["data"]

    # ------------------------------------------------------------------
    # POST /execucoes/{id}/cancelar
    # ------------------------------------------------------------------

    def test_cancelar_em_execucao(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.EM_EXECUCAO)

        response = client.post(f"/api/v1/execucoes/{exec_.id}/cancelar")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == ExecucaoStatus.CANCELADO.value

    def test_cancelar_ja_concluido(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        response = client.post(f"/api/v1/execucoes/{exec_.id}/cancelar")

        assert response.status_code == 409

    def test_cancelar_nao_existe(self, client):
        response = client.post(f"/api/v1/execucoes/{uuid4()}/cancelar")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # POST /execucoes/{id}/pausar
    # ------------------------------------------------------------------

    def test_pausar_em_execucao(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.EM_EXECUCAO)

        response = client.post(f"/api/v1/execucoes/{exec_.id}/pausar")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == ExecucaoStatus.PAUSADO.value

    def test_pausar_invalido(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        response = client.post(f"/api/v1/execucoes/{exec_.id}/pausar")

        assert response.status_code == 409

    # ------------------------------------------------------------------
    # POST /execucoes/{id}/retomar
    # ------------------------------------------------------------------

    def test_retomar_pausado(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.PAUSADO)

        response = client.post(f"/api/v1/execucoes/{exec_.id}/retomar")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == ExecucaoStatus.EM_EXECUCAO.value

    def test_retomar_nao_pausado(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.AGUARDANDO)

        response = client.post(f"/api/v1/execucoes/{exec_.id}/retomar")

        assert response.status_code == 409

    # ------------------------------------------------------------------
    # GET /execucoes/{id}/progresso
    # ------------------------------------------------------------------

    def test_get_progresso(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.EM_EXECUCAO)

        response = client.get(f"/api/v1/execucoes/{exec_.id}/progresso")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["execucao_id"] == str(exec_.id)
        assert "progresso_percentual" in data["data"]

    def test_get_progresso_nao_existe(self, client):
        response = client.get(f"/api/v1/execucoes/{uuid4()}/progresso")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /execucoes/{id}/metricas
    # ------------------------------------------------------------------

    def test_get_metricas(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        response = client.get(f"/api/v1/execucoes/{exec_.id}/metricas")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["execucao_id"] == str(exec_.id)
        assert "taxa_sucesso" in data["data"]

    # ------------------------------------------------------------------
    # DELETE /execucoes/{id}
    # ------------------------------------------------------------------

    def test_delete_sucesso(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        response = client.delete(f"/api/v1/execucoes/{exec_.id}")

        assert response.status_code == 204

    def test_delete_em_execucao_bloqueado(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.EM_EXECUCAO)

        response = client.delete(f"/api/v1/execucoes/{exec_.id}")

        assert response.status_code == 409

    def test_delete_nao_existe(self, client):
        response = client.delete(f"/api/v1/execucoes/{uuid4()}")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # PATCH /execucoes/{id}/status
    # ------------------------------------------------------------------

    def test_update_status_valido(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.AGUARDANDO)

        response = client.patch(
            f"/api/v1/execucoes/{exec_.id}/status",
            json={"status": "em_execucao"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == ExecucaoStatus.EM_EXECUCAO.value

    def test_update_status_invalido(self, client, execucao_factory):
        exec_ = execucao_factory(status=ExecucaoStatus.CONCLUIDO)

        response = client.patch(
            f"/api/v1/execucoes/{exec_.id}/status",
            json={"status": "em_execucao"},
        )

        assert response.status_code == 400
