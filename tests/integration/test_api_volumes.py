"""Testes de integração para API de Volumes."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.configuracao import Configuracao
from toninho.models.enums import (
    AgendamentoTipo,
    FormatoSaida,
    VolumeStatus,
    VolumeTipo,
)
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
def volume_factory(db):
    """Factory para criar volumes no banco de teste."""
    counter = {"value": 0}

    def _create(**kwargs):
        counter["value"] += 1
        defaults = {
            "nome": f"Volume Integ {counter['value']}",
            "path": f"/tmp/integ-vol-{counter['value']}",
            "tipo": VolumeTipo.LOCAL,
            "status": VolumeStatus.ATIVO,
        }
        defaults.update(kwargs)
        vol = Volume(**defaults)
        db.add(vol)
        db.commit()
        db.refresh(vol)
        return vol

    return _create


# ---------------------------------------------------------------------------
# Tests — CREATE
# ---------------------------------------------------------------------------


class TestVolumeAPICreate:
    def test_criar_volume_sucesso(self, client, tmp_path):
        payload = {
            "nome": "Vol API Create",
            "path": str(tmp_path / "create-test"),
            "descricao": "Criado via API",
        }
        resp = client.post("/api/v1/volumes", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["nome"] == payload["nome"]
        assert data["data"]["tipo"] == "local"
        assert data["data"]["status"] == "ativo"

    def test_criar_volume_nome_duplicado(self, client, volume_factory, tmp_path):
        volume_factory(nome="Duplicado")
        payload = {
            "nome": "Duplicado",
            "path": str(tmp_path / "dup-test"),
        }
        resp = client.post("/api/v1/volumes", json=payload)
        assert resp.status_code == 409

    def test_criar_volume_path_duplicado(self, client, volume_factory):
        volume_factory(path="/tmp/dup-path")
        payload = {
            "nome": "Outro Nome",
            "path": "/tmp/dup-path",
        }
        resp = client.post("/api/v1/volumes", json=payload)
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Tests — LIST
# ---------------------------------------------------------------------------


class TestVolumeAPIList:
    def test_listar_volumes(self, client, volume_factory):
        volume_factory()
        volume_factory()

        resp = client.get("/api/v1/volumes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 2
        assert data["meta"]["total"] >= 2

    def test_listar_com_paginacao(self, client, volume_factory):
        for _ in range(5):
            volume_factory()

        resp = client.get("/api/v1/volumes?page=1&per_page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["meta"]["total"] == 5

    def test_listar_com_busca(self, client, volume_factory):
        volume_factory(nome="Busca Alvo XYZ")
        volume_factory(nome="Outro Qualquer")

        resp = client.get("/api/v1/volumes?busca=XYZ")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        assert "XYZ" in data["data"][0]["nome"]

    def test_listar_ativos(self, client, volume_factory):
        volume_factory(status=VolumeStatus.ATIVO)
        volume_factory(status=VolumeStatus.INATIVO)

        resp = client.get("/api/v1/volumes/ativos")
        assert resp.status_code == 200
        data = resp.json()
        assert all(v["status"] == "ativo" for v in data["data"])


# ---------------------------------------------------------------------------
# Tests — GET
# ---------------------------------------------------------------------------


class TestVolumeAPIGet:
    def test_obter_volume(self, client, volume_factory):
        vol = volume_factory()
        resp = client.get(f"/api/v1/volumes/{vol.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["id"] == str(vol.id)
        assert data["data"]["nome"] == vol.nome

    def test_obter_volume_nao_encontrado(self, client):
        resp = client.get(f"/api/v1/volumes/{uuid4()}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — UPDATE
# ---------------------------------------------------------------------------


class TestVolumeAPIUpdate:
    def test_atualizar_nome(self, client, volume_factory):
        vol = volume_factory()
        resp = client.put(
            f"/api/v1/volumes/{vol.id}",
            json={"nome": "Nome Atualizado"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["nome"] == "Nome Atualizado"

    def test_atualizar_status(self, client, volume_factory):
        vol = volume_factory()
        resp = client.put(
            f"/api/v1/volumes/{vol.id}",
            json={"status": "inativo"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "inativo"

    def test_atualizar_volume_nao_encontrado(self, client):
        resp = client.put(
            f"/api/v1/volumes/{uuid4()}",
            json={"nome": "Novo"},
        )
        assert resp.status_code == 404

    def test_atualizar_nome_duplicado(self, client, volume_factory):
        volume_factory(nome="Existente")
        vol2 = volume_factory(nome="Outro")

        resp = client.put(
            f"/api/v1/volumes/{vol2.id}",
            json={"nome": "Existente"},
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Tests — DELETE
# ---------------------------------------------------------------------------


class TestVolumeAPIDelete:
    def test_deletar_volume(self, client, volume_factory):
        vol = volume_factory()
        resp = client.delete(f"/api/v1/volumes/{vol.id}")
        assert resp.status_code == 204

        # Confirma que não existe mais
        resp = client.get(f"/api/v1/volumes/{vol.id}")
        assert resp.status_code == 404

    def test_deletar_volume_nao_encontrado(self, client):
        resp = client.delete(f"/api/v1/volumes/{uuid4()}")
        assert resp.status_code == 404

    def test_deletar_volume_com_configuracoes(self, client, volume_factory, db):
        vol = volume_factory()

        processo = Processo(nome="Proc Vinc", descricao="desc")
        db.add(processo)
        db.commit()
        db.refresh(processo)

        config = Configuracao(
            processo_id=processo.id,
            volume_id=vol.id,
            urls=["https://example.com"],
            formato_saida=FormatoSaida.ARQUIVO_UNICO,
            agendamento_tipo=AgendamentoTipo.MANUAL,
        )
        db.add(config)
        db.commit()

        resp = client.delete(f"/api/v1/volumes/{vol.id}")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Tests — TESTAR & VALIDAR
# ---------------------------------------------------------------------------


class TestVolumeAPIValidation:
    def test_testar_volume(self, client, volume_factory, tmp_path):
        vol = volume_factory(path=str(tmp_path))
        resp = client.post(f"/api/v1/volumes/{vol.id}/testar")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["valido"] is True
        assert data["pode_ler"] is True
        assert data["pode_escrever"] is True

    def test_testar_volume_nao_encontrado(self, client):
        resp = client.post(f"/api/v1/volumes/{uuid4()}/testar")
        assert resp.status_code == 404

    def test_validar_path(self, client, tmp_path):
        resp = client.post(
            "/api/v1/volumes/validar-path",
            json={"path": str(tmp_path)},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["valido"] is True
