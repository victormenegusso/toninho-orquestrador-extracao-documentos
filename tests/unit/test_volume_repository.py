"""Testes unitários para VolumeRepository."""

from uuid import uuid4

import pytest

from toninho.models.configuracao import Configuracao
from toninho.models.enums import (
    AgendamentoTipo,
    FormatoSaida,
    VolumeStatus,
    VolumeTipo,
)
from toninho.models.processo import Processo
from toninho.models.volume import Volume
from toninho.repositories.volume_repository import VolumeRepository


class TestVolumeRepository:
    """Testes para VolumeRepository."""

    @pytest.fixture
    def repository(self):
        return VolumeRepository()

    @pytest.fixture
    def volume_data(self):
        return {
            "nome": "Volume Repo Teste",
            "path": "/tmp/repo-test",
            "tipo": VolumeTipo.LOCAL,
            "status": VolumeStatus.ATIVO,
            "descricao": "Volume para testes de repository",
        }

    @pytest.fixture
    def saved_volume(self, db, repository, volume_data):
        vol = Volume(**volume_data)
        return repository.create(db, vol)

    # ── CREATE ────────────────────────────────────────────────────────

    def test_create_retorna_volume_com_id(self, db, repository, volume_data):
        vol = Volume(**volume_data)
        result = repository.create(db, vol)

        assert result.id is not None
        assert result.nome == volume_data["nome"]
        assert result.path == volume_data["path"]
        assert result.tipo == VolumeTipo.LOCAL
        assert result.status == VolumeStatus.ATIVO

    # ── GET BY ID ─────────────────────────────────────────────────────

    def test_get_by_id_encontrado(self, db, repository, saved_volume):
        result = repository.get_by_id(db, saved_volume.id)
        assert result is not None
        assert result.id == saved_volume.id

    def test_get_by_id_nao_encontrado(self, db, repository):
        result = repository.get_by_id(db, uuid4())
        assert result is None

    # ── GET BY NOME ───────────────────────────────────────────────────

    def test_get_by_nome_encontrado(self, db, repository, saved_volume):
        result = repository.get_by_nome(db, saved_volume.nome)
        assert result is not None
        assert result.nome == saved_volume.nome

    def test_get_by_nome_nao_encontrado(self, db, repository):
        result = repository.get_by_nome(db, "Inexistente")
        assert result is None

    # ── GET BY PATH ───────────────────────────────────────────────────

    def test_get_by_path_encontrado(self, db, repository, saved_volume):
        result = repository.get_by_path(db, saved_volume.path)
        assert result is not None
        assert result.path == saved_volume.path

    def test_get_by_path_nao_encontrado(self, db, repository):
        result = repository.get_by_path(db, "/caminho/inexistente")
        assert result is None

    # ── GET ALL ───────────────────────────────────────────────────────

    def test_get_all_retorna_lista_e_total(self, db, repository, saved_volume):
        volumes, total = repository.get_all(db)
        assert total >= 1
        assert len(volumes) >= 1

    def test_get_all_com_paginacao(self, db, repository):
        for i in range(5):
            repository.create(
                db,
                Volume(
                    nome=f"Vol Pag {i}",
                    path=f"/tmp/pag-{i}",
                    tipo=VolumeTipo.LOCAL,
                    status=VolumeStatus.ATIVO,
                ),
            )

        volumes, total = repository.get_all(db, skip=0, limit=2)
        assert total == 5
        assert len(volumes) == 2

    def test_get_all_filtra_por_status(self, db, repository):
        repository.create(
            db,
            Volume(
                nome="Ativo",
                path="/tmp/ativo",
                tipo=VolumeTipo.LOCAL,
                status=VolumeStatus.ATIVO,
            ),
        )
        repository.create(
            db,
            Volume(
                nome="Inativo",
                path="/tmp/inativo",
                tipo=VolumeTipo.LOCAL,
                status=VolumeStatus.INATIVO,
            ),
        )

        volumes, total = repository.get_all(db, status=VolumeStatus.ATIVO)
        assert total == 1
        assert all(v.status == VolumeStatus.ATIVO for v in volumes)

    def test_get_all_filtra_por_busca(self, db, repository):
        repository.create(
            db,
            Volume(
                nome="Produção Alpha",
                path="/tmp/prod-alpha",
                tipo=VolumeTipo.LOCAL,
                status=VolumeStatus.ATIVO,
            ),
        )
        repository.create(
            db,
            Volume(
                nome="Teste Beta",
                path="/tmp/test-beta",
                tipo=VolumeTipo.LOCAL,
                status=VolumeStatus.ATIVO,
            ),
        )

        volumes, total = repository.get_all(db, busca="Alpha")
        assert total == 1
        assert volumes[0].nome == "Produção Alpha"

    # ── GET ATIVOS ────────────────────────────────────────────────────

    def test_get_ativos_retorna_apenas_ativos(self, db, repository):
        repository.create(
            db,
            Volume(
                nome="Ativo 1",
                path="/tmp/ativo1",
                tipo=VolumeTipo.LOCAL,
                status=VolumeStatus.ATIVO,
            ),
        )
        repository.create(
            db,
            Volume(
                nome="Inativo 1",
                path="/tmp/inativo1",
                tipo=VolumeTipo.LOCAL,
                status=VolumeStatus.INATIVO,
            ),
        )

        ativos = repository.get_ativos(db)
        assert len(ativos) == 1
        assert ativos[0].nome == "Ativo 1"

    # ── UPDATE ────────────────────────────────────────────────────────

    def test_update_altera_campos(self, db, repository, saved_volume):
        saved_volume.nome = "Nome Atualizado"
        result = repository.update(db, saved_volume)
        assert result.nome == "Nome Atualizado"

    # ── DELETE ────────────────────────────────────────────────────────

    def test_delete_retorna_true(self, db, repository, saved_volume):
        result = repository.delete(db, saved_volume.id)
        assert result is True
        assert repository.get_by_id(db, saved_volume.id) is None

    def test_delete_nao_encontrado_retorna_false(self, db, repository):
        result = repository.delete(db, uuid4())
        assert result is False

    # ── EXISTS BY NOME ────────────────────────────────────────────────

    def test_exists_by_nome_retorna_true(self, db, repository, saved_volume):
        assert repository.exists_by_nome(db, saved_volume.nome) is True

    def test_exists_by_nome_retorna_false(self, db, repository):
        assert repository.exists_by_nome(db, "Não Existe") is False

    def test_exists_by_nome_com_exclude_id(self, db, repository, saved_volume):
        assert (
            repository.exists_by_nome(db, saved_volume.nome, exclude_id=saved_volume.id)
            is False
        )

    # ── EXISTS BY PATH ────────────────────────────────────────────────

    def test_exists_by_path_retorna_true(self, db, repository, saved_volume):
        assert repository.exists_by_path(db, saved_volume.path) is True

    def test_exists_by_path_retorna_false(self, db, repository):
        assert repository.exists_by_path(db, "/inexistente") is False

    def test_exists_by_path_com_exclude_id(self, db, repository, saved_volume):
        assert (
            repository.exists_by_path(db, saved_volume.path, exclude_id=saved_volume.id)
            is False
        )

    # ── COUNT CONFIGURAÇÕES ───────────────────────────────────────────

    def test_count_configuracoes_zero(self, db, repository, saved_volume):
        count = repository.count_configuracoes(db, saved_volume.id)
        assert count == 0

    def test_count_configuracoes_com_vinculos(self, db, repository, saved_volume):
        processo = Processo(nome="Proc Test", descricao="desc")
        db.add(processo)
        db.commit()
        db.refresh(processo)

        config = Configuracao(
            processo_id=processo.id,
            volume_id=saved_volume.id,
            urls=["https://example.com"],
            formato_saida=FormatoSaida.ARQUIVO_UNICO,
            agendamento_tipo=AgendamentoTipo.MANUAL,
        )
        db.add(config)
        db.commit()

        count = repository.count_configuracoes(db, saved_volume.id)
        assert count == 1
