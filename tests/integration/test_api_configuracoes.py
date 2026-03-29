"""Testes de integração para API de Configurações."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.configuracao import Configuracao
from toninho.models.enums import AgendamentoTipo, FormatoSaida, VolumeStatus, VolumeTipo
from toninho.models.processo import Processo
from toninho.models.volume import Volume

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
def volume(db):
    """Cria um volume para usar nos testes."""
    v = Volume(
        nome="Volume Config Teste",
        path="/tmp/config-test-output",
        tipo=VolumeTipo.LOCAL,
        status=VolumeStatus.ATIVO,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@pytest.fixture
def processo(db):
    """Cria um processo para usar nos testes."""
    p = Processo(nome="Processo Config Teste", descricao="desc")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def config_payload(volume):
    return {
        "urls": ["https://exemplo.com", "https://exemplo.com/pagina2"],
        "timeout": 3600,
        "max_retries": 3,
        "volume_id": str(volume.id),
        "agendamento_tipo": "manual",
    }


@pytest.fixture
def config_factory(db, processo, volume):
    """Factory para criar configurações diretamente no DB."""
    counter = {"value": 0}

    def _create(**kwargs):
        counter["value"] += 1
        defaults = {
            "processo_id": processo.id,
            "urls": ["https://exemplo.com"],
            "timeout": 3600,
            "max_retries": 3,
            "volume_id": volume.id,
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

    def test_create_urls_invalidas(self, client, processo, volume):
        payload = {
            "urls": ["nao-e-url"],
            "volume_id": str(volume.id),
            "agendamento_tipo": "manual",
        }
        response = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes",
            json=payload,
        )
        assert response.status_code == 422

    def test_create_cron_invalido_recorrente(self, client, processo, volume):
        payload = {
            "urls": ["https://exemplo.com"],
            "volume_id": str(volume.id),
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


# ── Passo 2 — API: metodo_extracao (UC-07, UC-08, UC-09) ─────────────────────


class TestConfigMetodoExtracao:
    """Testes de integração para metodo_extracao via API REST."""

    def test_post_com_docling_persiste_e_retorna(self, client, processo, volume):
        payload = {
            "urls": ["https://exemplo.com"],
            "timeout": 3600,
            "max_retries": 3,
            "volume_id": str(volume.id),
            "agendamento_tipo": "manual",
            "metodo_extracao": "docling",
        }
        resp = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes", json=payload
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["metodo_extracao"] == "docling"

    def test_post_sem_metodo_usa_html2text(self, client, processo, volume):
        payload = {
            "urls": ["https://exemplo.com"],
            "timeout": 3600,
            "max_retries": 3,
            "volume_id": str(volume.id),
            "agendamento_tipo": "manual",
        }
        resp = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes", json=payload
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["metodo_extracao"] == "html2text"

    def test_get_configuracao_retorna_metodo_extracao(self, client, config_factory):
        from toninho.models.enums import MetodoExtracao

        config = config_factory(metodo_extracao=MetodoExtracao.DOCLING)
        resp = client.get(f"/api/v1/processos/{config.processo_id}/configuracao")
        assert resp.status_code == 200
        assert resp.json()["data"]["metodo_extracao"] == "docling"

    def test_put_atualiza_metodo_de_html2text_para_docling(
        self, client, config_factory
    ):
        config = config_factory()  # default: html2text
        resp = client.put(
            f"/api/v1/configuracoes/{config.id}",
            json={"metodo_extracao": "docling"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["metodo_extracao"] == "docling"

    def test_put_com_metodo_invalido_retorna_422(self, client, config_factory):
        config = config_factory()
        resp = client.put(
            f"/api/v1/configuracoes/{config.id}",
            json={"metodo_extracao": "nao_existe"},
        )
        assert resp.status_code == 422
