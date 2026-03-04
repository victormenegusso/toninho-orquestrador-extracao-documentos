"""Testes de integração para API de Configurações."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.configuracao import Configuracao
from toninho.models.enums import AgendamentoTipo, FormatoSaida
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
    """Cria um processo para usar nos testes."""
    p = Processo(nome="Processo Config Teste", descricao="desc")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def config_payload():
    return {
        "urls": ["https://exemplo.com", "https://exemplo.com/pagina2"],
        "timeout": 3600,
        "max_retries": 3,
        "output_dir": "/tmp/output",
        "agendamento_tipo": "manual",
    }


@pytest.fixture
def config_factory(db, processo):
    """Factory para criar configurações diretamente no DB."""
    counter = {"value": 0}

    def _create(**kwargs):
        counter["value"] += 1
        defaults = {
            "processo_id": processo.id,
            "urls": ["https://exemplo.com"],
            "timeout": 3600,
            "max_retries": 3,
            "output_dir": "/tmp/output",
            "agendamento_tipo": AgendamentoTipo.MANUAL,
            "formato_saida": FormatoSaida.MULTIPLOS_ARQUIVOS,
        }
        defaults.update(kwargs)
        config = Configuracao(**defaults)
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    return _create


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestConfiguracaoAPI:
    # ------------------------------------------------------------------
    # POST /processos/{id}/configuracoes
    # ------------------------------------------------------------------

    def test_create_sucesso(self, client, processo, config_payload):
        response = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes",
            json=config_payload,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["processo_id"] == str(processo.id)
        assert data["data"]["timeout"] == 3600

    def test_create_processo_nao_existe(self, client, config_payload):
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/processos/{fake_id}/configuracoes",
            json=config_payload,
        )
        assert response.status_code == 404

    def test_create_urls_invalidas(self, client, processo):
        payload = {
            "urls": ["nao-e-url"],
            "output_dir": "/tmp",
            "agendamento_tipo": "manual",
        }
        response = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes",
            json=payload,
        )
        assert response.status_code == 422

    def test_create_cron_invalido_recorrente(self, client, processo):
        payload = {
            "urls": ["https://exemplo.com"],
            "output_dir": "/tmp",
            "agendamento_tipo": "recorrente",
            "agendamento_cron": None,
        }
        response = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes",
            json=payload,
        )
        assert response.status_code == 422

    # ------------------------------------------------------------------
    # GET /processos/{id}/configuracoes
    # ------------------------------------------------------------------

    def test_list_configuracoes(self, client, processo, config_factory):
        config_factory()
        config_factory()

        response = client.get(f"/api/v1/processos/{processo.id}/configuracoes")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 2

    def test_list_configuracoes_processo_nao_existe(self, client):
        response = client.get(f"/api/v1/processos/{uuid4()}/configuracoes")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /processos/{id}/configuracao (mais recente)
    # ------------------------------------------------------------------

    def test_get_configuracao_atual(self, client, processo, config_factory, db):
        c1 = config_factory(timeout=1111)
        # Força c1 a ser mais antigo para garantir ordenação
        from datetime import datetime, timedelta

        c1.created_at = datetime.now() - timedelta(seconds=10)
        db.add(c1)
        db.commit()

        config_factory(timeout=2222)  # mais recente

        response = client.get(f"/api/v1/processos/{processo.id}/configuracao")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["timeout"] == 2222

    def test_get_configuracao_sem_config(self, client, db):
        """Processo sem configuração retorna 404."""
        p = Processo(nome="Processo Sem Config")
        db.add(p)
        db.commit()
        db.refresh(p)

        response = client.get(f"/api/v1/processos/{p.id}/configuracao")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /configuracoes/{id}
    # ------------------------------------------------------------------

    def test_get_configuracao_por_id(self, client, config_factory):
        config = config_factory()

        response = client.get(f"/api/v1/configuracoes/{config.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(config.id)

    def test_get_configuracao_nao_existe(self, client):
        response = client.get(f"/api/v1/configuracoes/{uuid4()}")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # PUT /configuracoes/{id}
    # ------------------------------------------------------------------

    def test_update_configuracao(self, client, config_factory):
        config = config_factory(timeout=1234)

        response = client.put(
            f"/api/v1/configuracoes/{config.id}",
            json={"timeout": 9999},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["timeout"] == 9999

    def test_update_nao_existe(self, client):
        response = client.put(
            f"/api/v1/configuracoes/{uuid4()}",
            json={"timeout": 9999},
        )
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # DELETE /configuracoes/{id}
    # ------------------------------------------------------------------

    def test_delete_configuracao(self, client, config_factory):
        config = config_factory()

        response = client.delete(f"/api/v1/configuracoes/{config.id}")

        assert response.status_code == 204

    def test_delete_nao_existe(self, client):
        response = client.delete(f"/api/v1/configuracoes/{uuid4()}")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /configuracoes/{id}/validar-agendamento
    # ------------------------------------------------------------------

    def test_validar_agendamento_cron_valido(self, client, config_factory):
        config = config_factory(
            agendamento_tipo=AgendamentoTipo.RECORRENTE,
            agendamento_cron="0 2 * * *",
        )

        response = client.get(f"/api/v1/configuracoes/{config.id}/validar-agendamento")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["valida"] is True
        assert len(data["data"]["proximas_execucoes"]) == 5

    def test_validar_agendamento_sem_cron(self, client, config_factory):
        config = config_factory()

        response = client.get(f"/api/v1/configuracoes/{config.id}/validar-agendamento")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["valida"] is False
