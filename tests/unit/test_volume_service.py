"""Testes unitários para VolumeService."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import VolumeStatus, VolumeTipo
from toninho.models.volume import Volume
from toninho.repositories.volume_repository import VolumeRepository
from toninho.schemas.volume import (
    VolumeCreate,
    VolumeUpdate,
    VolumeValidationResult,
)
from toninho.services.volume_service import VolumeService

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_repo():
    return MagicMock(spec=VolumeRepository)


@pytest.fixture
def service(mock_repo):
    return VolumeService(repository=mock_repo)


@pytest.fixture
def volume_id():
    return uuid4()


@pytest.fixture
def fake_volume(volume_id):
    vol = MagicMock(spec=Volume)
    vol.id = volume_id
    vol.nome = "Volume Teste"
    vol.path = "/tmp/test"
    vol.tipo = VolumeTipo.LOCAL
    vol.status = VolumeStatus.ATIVO
    vol.descricao = "Descrição teste"
    vol.created_at = datetime.now(tz=UTC)
    vol.updated_at = datetime.now(tz=UTC)
    return vol


@pytest.fixture
def mock_db():
    return MagicMock()


# ── CREATE ────────────────────────────────────────────────────────────────────


class TestCreateVolume:
    def test_create_sucesso(self, service, mock_repo, fake_volume, mock_db):
        mock_repo.exists_by_nome.return_value = False
        mock_repo.exists_by_path.return_value = False
        mock_repo.create.return_value = fake_volume
        mock_repo.count_configuracoes.return_value = 0

        with patch.object(service, "validate_path_access") as mock_validate:
            mock_validate.return_value = VolumeValidationResult(
                path="/tmp/test",
                valido=True,
                pode_ler=True,
                pode_escrever=True,
                existe=True,
                criado=False,
            )

            data = VolumeCreate(nome="Volume Teste", path="/tmp/test")
            result = service.create_volume(mock_db, data)

            assert result.nome == "Volume Teste"
            mock_repo.create.assert_called_once()

    def test_create_nome_duplicado_lanca_conflict(self, service, mock_repo, mock_db):
        mock_repo.exists_by_nome.return_value = True

        data = VolumeCreate(nome="Duplicado", path="/tmp/dup")
        with pytest.raises(ConflictError, match="nome"):
            service.create_volume(mock_db, data)

    def test_create_path_duplicado_lanca_conflict(self, service, mock_repo, mock_db):
        mock_repo.exists_by_nome.return_value = False
        mock_repo.exists_by_path.return_value = True

        data = VolumeCreate(nome="Novo", path="/tmp/dup-path")
        with pytest.raises(ConflictError, match="path"):
            service.create_volume(mock_db, data)

    def test_create_path_invalido_lanca_validation(self, service, mock_repo, mock_db):
        mock_repo.exists_by_nome.return_value = False
        mock_repo.exists_by_path.return_value = False

        with patch.object(service, "validate_path_access") as mock_validate:
            mock_validate.return_value = VolumeValidationResult(
                path="/invalid",
                valido=False,
                pode_ler=False,
                pode_escrever=False,
                existe=False,
                criado=False,
                erro="Permissão negada",
            )

            data = VolumeCreate(nome="Volume", path="/invalid")
            with pytest.raises(ValidationError, match="acessível"):
                service.create_volume(mock_db, data)


# ── GET ───────────────────────────────────────────────────────────────────────


class TestGetVolume:
    def test_get_sucesso(self, service, mock_repo, fake_volume, volume_id, mock_db):
        mock_repo.get_by_id.return_value = fake_volume
        mock_repo.count_configuracoes.return_value = 2

        result = service.get_volume(mock_db, volume_id)
        assert result.nome == "Volume Teste"
        assert result.total_processos == 2

    def test_get_nao_encontrado_lanca_not_found(self, service, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_volume(mock_db, uuid4())


# ── LIST ──────────────────────────────────────────────────────────────────────


class TestListVolumes:
    def test_list_sucesso(self, service, mock_repo, fake_volume, mock_db):
        mock_repo.get_all.return_value = ([fake_volume], 1)
        mock_repo.count_configuracoes.return_value = 0

        result = service.list_volumes(mock_db, page=1, per_page=20)
        assert len(result.data) == 1
        assert result.meta.total == 1

    def test_list_pagina_invalida_lanca_validation(self, service, mock_db):
        with pytest.raises(ValidationError):
            service.list_volumes(mock_db, page=0)

    def test_list_per_page_invalido_lanca_validation(self, service, mock_db):
        with pytest.raises(ValidationError):
            service.list_volumes(mock_db, per_page=101)

    def test_list_com_filtros(self, service, mock_repo, fake_volume, mock_db):
        mock_repo.get_all.return_value = ([fake_volume], 1)
        mock_repo.count_configuracoes.return_value = 0

        result = service.list_volumes(
            mock_db,
            status=VolumeStatus.ATIVO,
            busca="Teste",
        )

        mock_repo.get_all.assert_called_once_with(
            db=mock_db,
            skip=0,
            limit=20,
            status=VolumeStatus.ATIVO,
            busca="Teste",
        )
        assert len(result.data) == 1


# ── GET ATIVOS ────────────────────────────────────────────────────────────────


class TestGetVolumesAtivos:
    def test_get_ativos_retorna_summaries(
        self, service, mock_repo, fake_volume, mock_db
    ):
        mock_repo.get_ativos.return_value = [fake_volume]

        result = service.get_volumes_ativos(mock_db)
        assert len(result) == 1
        assert result[0].nome == "Volume Teste"


# ── UPDATE ────────────────────────────────────────────────────────────────────


class TestUpdateVolume:
    def test_update_nome_sucesso(
        self, service, mock_repo, fake_volume, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = fake_volume
        mock_repo.exists_by_nome.return_value = False
        mock_repo.update.return_value = fake_volume
        mock_repo.count_configuracoes.return_value = 0

        data = VolumeUpdate(nome="Novo Nome")
        result = service.update_volume(mock_db, volume_id, data)
        assert result is not None
        mock_repo.update.assert_called_once()

    def test_update_nao_encontrado_lanca_not_found(self, service, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None

        data = VolumeUpdate(nome="Novo")
        with pytest.raises(NotFoundError):
            service.update_volume(mock_db, uuid4(), data)

    def test_update_sem_campos_lanca_validation(
        self, service, mock_repo, fake_volume, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = fake_volume

        data = VolumeUpdate()
        with pytest.raises(ValidationError, match="Nenhum campo"):
            service.update_volume(mock_db, volume_id, data)

    def test_update_nome_duplicado_lanca_conflict(
        self, service, mock_repo, fake_volume, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = fake_volume
        mock_repo.exists_by_nome.return_value = True
        fake_volume.nome = "Nome Antigo"

        data = VolumeUpdate(nome="Nome Existente")
        with pytest.raises(ConflictError, match="nome"):
            service.update_volume(mock_db, volume_id, data)

    def test_update_path_duplicado_lanca_conflict(
        self, service, mock_repo, fake_volume, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = fake_volume
        mock_repo.exists_by_path.return_value = True
        fake_volume.path = "/tmp/antigo"

        data = VolumeUpdate(path="/tmp/outro-existente")
        with pytest.raises(ConflictError, match="path"):
            service.update_volume(mock_db, volume_id, data)

    def test_update_path_invalido_lanca_validation(
        self, service, mock_repo, fake_volume, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = fake_volume
        mock_repo.exists_by_path.return_value = False
        fake_volume.path = "/tmp/antigo"

        with patch.object(service, "validate_path_access") as mock_validate:
            mock_validate.return_value = VolumeValidationResult(
                path="/invalido",
                valido=False,
                pode_ler=False,
                pode_escrever=False,
                existe=False,
                criado=False,
                erro="Erro",
            )

            data = VolumeUpdate(path="/invalido")
            with pytest.raises(ValidationError, match="acessível"):
                service.update_volume(mock_db, volume_id, data)

    def test_update_path_com_acesso_valido(
        self, service, mock_repo, fake_volume, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = fake_volume
        mock_repo.exists_by_path.return_value = False
        mock_repo.update.return_value = fake_volume
        mock_repo.count_configuracoes.return_value = 0
        fake_volume.path = "/tmp/antigo"

        with patch.object(service, "validate_path_access") as mock_validate:
            mock_validate.return_value = VolumeValidationResult(
                path="/tmp/novo",
                valido=True,
                pode_ler=True,
                pode_escrever=True,
                existe=True,
                criado=False,
            )

            data = VolumeUpdate(path="/tmp/novo")
            result = service.update_volume(mock_db, volume_id, data)
            assert result is not None


# ── DELETE ────────────────────────────────────────────────────────────────────


class TestDeleteVolume:
    def test_delete_sucesso(self, service, mock_repo, volume_id, mock_db):
        mock_repo.get_by_id.return_value = MagicMock()
        mock_repo.count_configuracoes.return_value = 0
        mock_repo.delete.return_value = True

        result = service.delete_volume(mock_db, volume_id)
        assert result is True

    def test_delete_nao_encontrado_lanca_not_found(self, service, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_volume(mock_db, uuid4())

    def test_delete_com_configuracoes_lanca_conflict(
        self, service, mock_repo, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = MagicMock()
        mock_repo.count_configuracoes.return_value = 3

        with pytest.raises(ConflictError, match="configuração"):
            service.delete_volume(mock_db, volume_id)


# ── TEST VOLUME ───────────────────────────────────────────────────────────────


class TestTestVolume:
    def test_test_volume_sucesso(
        self, service, mock_repo, fake_volume, volume_id, mock_db
    ):
        mock_repo.get_by_id.return_value = fake_volume

        with patch.object(service, "validate_path_access") as mock_validate:
            mock_validate.return_value = VolumeValidationResult(
                path="/tmp/test",
                valido=True,
                pode_ler=True,
                pode_escrever=True,
                existe=True,
                criado=False,
            )

            result = service.test_volume(mock_db, volume_id)
            assert result.valido is True

    def test_test_volume_nao_encontrado(self, service, mock_repo, mock_db):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.test_volume(mock_db, uuid4())


# ── VALIDATE PATH ACCESS ─────────────────────────────────────────────────────


class TestValidatePathAccess:
    def test_validate_path_existente_com_permissao(self, service, tmp_path):
        result = service.validate_path_access(str(tmp_path))
        assert result.valido is True
        assert result.pode_ler is True
        assert result.pode_escrever is True
        assert result.existe is True
        assert result.criado is False
        assert result.erro is None

    def test_validate_path_cria_diretorio(self, service, tmp_path):
        new_dir = str(tmp_path / "novo_dir")
        result = service.validate_path_access(new_dir)
        assert result.valido is True
        assert result.criado is True
        assert result.existe is True

    def test_validate_path_sem_permissao_criar(self, service):
        with (
            patch("os.path.isdir", return_value=False),
            patch("os.makedirs", side_effect=OSError("Permission denied")),
        ):
            result = service.validate_path_access("/root/proibido")
            assert result.valido is False
            assert result.criado is False
            assert result.erro is not None
            assert "criar" in result.erro

    def test_validate_path_sem_permissao_escrita(self, service, tmp_path):
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = service.validate_path_access(str(tmp_path))
            assert result.valido is False
            assert result.pode_escrever is False
            assert result.erro is not None
            assert "escrita" in result.erro

    def test_validate_path_sem_permissao_leitura(self, service, tmp_path):
        call_count = 0
        original_open = open

        def side_effect_open(path, *args, **kwargs):
            nonlocal call_count
            if str(path).endswith(".toninho_volume_test"):
                call_count += 1
                if call_count == 1:
                    return original_open(path, *args, **kwargs)
                raise OSError("Permission denied")
            return original_open(path, *args, **kwargs)

        with patch("builtins.open", side_effect=side_effect_open):
            result = service.validate_path_access(str(tmp_path))
            assert result.valido is False
            assert result.pode_escrever is True
            assert result.erro is not None
            assert "leitura" in result.erro

    def test_validate_path_erro_inesperado(self, service):
        with (
            patch("os.path.normpath", return_value="/qualquer"),
            patch("os.path.isdir", return_value=True),
            patch("builtins.open", side_effect=RuntimeError("Boom")),
        ):
            result = service.validate_path_access("/qualquer")
            assert result.valido is False
            assert "inesperado" in result.erro.lower()
