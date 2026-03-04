"""Testes de integração para API de Logs."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.enums import ExecucaoStatus, LogNivel
from toninho.models.execucao import Execucao
from toninho.models.log import Log
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
    p = Processo(nome="Processo Log API Teste", descricao="desc")
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
def log_factory(db, execucao):
    counter = {"value": 0}

    def _create(**kwargs):
        counter["value"] += 1
        defaults = {
            "execucao_id": execucao.id,
            "nivel": LogNivel.INFO,
            "mensagem": f"Mensagem de teste {counter['value']}",
        }
        defaults.update(kwargs)
        log = Log(**defaults)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    return _create


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestLogsAPI:
    # ------------------------------------------------------------------
    # POST /api/v1/logs
    # ------------------------------------------------------------------

    def test_create_log_sucesso(self, client, execucao):
        payload = {
            "execucao_id": str(execucao.id),
            "nivel": "info",
            "mensagem": "Log de teste via API",
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["mensagem"] == "Log de teste via API"
        assert data["data"]["nivel"] == "info"

    def test_create_log_com_contexto(self, client, execucao):
        payload = {
            "execucao_id": str(execucao.id),
            "nivel": "debug",
            "mensagem": "Log debug",
            "contexto": {"url": "https://teste.com", "status_code": 200},
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["contexto"]["url"] == "https://teste.com"

    def test_create_log_execucao_inexistente(self, client):
        payload = {
            "execucao_id": str(uuid4()),
            "nivel": "info",
            "mensagem": "Log",
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # POST /api/v1/logs/batch
    # ------------------------------------------------------------------

    def test_create_log_batch_sucesso(self, client, execucao):
        payload = [
            {"execucao_id": str(execucao.id), "nivel": "info", "mensagem": "Log 1"},
            {"execucao_id": str(execucao.id), "nivel": "warning", "mensagem": "Log 2"},
            {"execucao_id": str(execucao.id), "nivel": "error", "mensagem": "Log 3"},
        ]
        response = client.post("/api/v1/logs/batch", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3

    def test_create_log_batch_execucao_inexistente(self, client, execucao):
        payload = [
            {"execucao_id": str(execucao.id), "nivel": "info", "mensagem": "Log 1"},
            {"execucao_id": str(uuid4()), "nivel": "info", "mensagem": "Log 2"},
        ]
        response = client.post("/api/v1/logs/batch", json=payload)
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/execucoes/{id}/logs
    # ------------------------------------------------------------------

    def test_list_logs_sucesso(self, client, log_factory, execucao):
        log_factory()
        log_factory()

        response = client.get(f"/api/v1/execucoes/{execucao.id}/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 2

    def test_list_logs_filtro_nivel(self, client, log_factory, execucao):
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.ERROR)

        response = client.get(f"/api/v1/execucoes/{execucao.id}/logs?nivel=error")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 1
        assert data["data"][0]["nivel"] == "error"

    def test_list_logs_filtro_busca(self, client, log_factory, execucao):
        log_factory(mensagem="Página extraída com sucesso")
        log_factory(mensagem="Erro ao processar URL")

        response = client.get(f"/api/v1/execucoes/{execucao.id}/logs?busca=extraída")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 1

    def test_list_logs_paginacao(self, client, log_factory, execucao):
        for _ in range(5):
            log_factory()

        response = client.get(f"/api/v1/execucoes/{execucao.id}/logs?page=1&per_page=3")
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["total"] == 5
        assert len(data["data"]) == 3
        assert data["meta"]["total_pages"] == 2

    def test_list_logs_execucao_inexistente(self, client):
        response = client.get(f"/api/v1/execucoes/{uuid4()}/logs")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/execucoes/{id}/logs/recentes
    # ------------------------------------------------------------------

    def test_get_logs_recentes(self, client, log_factory, execucao):
        for _ in range(5):
            log_factory()

        response = client.get(f"/api/v1/execucoes/{execucao.id}/logs/recentes?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3

    def test_get_logs_recentes_execucao_inexistente(self, client):
        response = client.get(f"/api/v1/execucoes/{uuid4()}/logs/recentes")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/execucoes/{id}/logs/estatisticas
    # ------------------------------------------------------------------

    def test_get_estatisticas_logs(self, client, log_factory, execucao):
        log_factory(nivel=LogNivel.INFO)
        log_factory(nivel=LogNivel.ERROR)

        response = client.get(f"/api/v1/execucoes/{execucao.id}/logs/estatisticas")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 2
        assert data["data"]["percentual_erros"] == 50.0

    def test_get_estatisticas_logs_execucao_inexistente(self, client):
        response = client.get(f"/api/v1/execucoes/{uuid4()}/logs/estatisticas")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/logs/{id}
    # ------------------------------------------------------------------

    def test_get_log_por_id(self, client, log_factory):
        log = log_factory()
        response = client.get(f"/api/v1/logs/{log.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(log.id)

    def test_get_log_nao_encontrado(self, client):
        response = client.get(f"/api/v1/logs/{uuid4()}")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /api/v1/execucoes/{id}/logs/stream
    # ------------------------------------------------------------------

    def test_stream_logs_execucao_inexistente(self, client):
        response = client.get(f"/api/v1/execucoes/{uuid4()}/logs/stream")
        assert response.status_code == 404

    def test_stream_logs_execucao_finalizada(self, client, db, processo):
        """SSE deve emitir evento done quando execução está em estado final."""
        from toninho.models.enums import ExecucaoStatus

        execucao_final = Execucao(
            processo_id=processo.id,
            status=ExecucaoStatus.CONCLUIDO,
            paginas_processadas=0,
            bytes_extraidos=0,
            taxa_erro=0.0,
        )
        db.add(execucao_final)
        db.commit()
        db.refresh(execucao_final)

        response = client.get(f"/api/v1/execucoes/{execucao_final.id}/logs/stream")
        assert response.status_code == 200
        content = response.text
        assert "done" in content
