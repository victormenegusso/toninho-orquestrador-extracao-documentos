"""Testes unitários para ConfiguracaoRepository."""

from uuid import uuid4

import pytest

from toninho.models.configuracao import Configuracao
from toninho.models.enums import AgendamentoTipo, FormatoSaida, VolumeStatus, VolumeTipo
from toninho.models.processo import Processo
from toninho.models.volume import Volume
from toninho.repositories.configuracao_repository import ConfiguracaoRepository


class TestConfiguracaoRepository:
    """Testes para ConfiguracaoRepository."""

    @pytest.fixture
    def repository(self):
        return ConfiguracaoRepository()

    @pytest.fixture
    def processo(self, db):
        """Cria um processo para usar como FK."""
        p = Processo(nome="Processo Repo Teste", descricao="desc")
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    @pytest.fixture
    def volume(self, db):
        """Cria um volume para usar como FK."""
        v = Volume(
            nome="Volume Repo Teste",
            path="/tmp/repo-test-output",
            tipo=VolumeTipo.LOCAL,
            status=VolumeStatus.ATIVO,
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return v

    @pytest.fixture
    def config_data(self, processo, volume):
        return {
            "processo_id": processo.id,
            "urls": ["https://exemplo.com"],
            "timeout": 3600,
            "max_retries": 3,
            "formato_saida": FormatoSaida.MULTIPLOS_ARQUIVOS,
            "volume_id": volume.id,
            "agendamento_tipo": AgendamentoTipo.MANUAL,
        }

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    def test_create(self, db, repository, config_data):
        """Cria uma configuração e verifica persistência."""
        config = Configuracao(**config_data)
        result = repository.create(db, config)

        assert result.id is not None
        assert result.processo_id == config_data["processo_id"]
        assert result.urls == config_data["urls"]
        assert result.timeout == config_data["timeout"]
        assert result.created_at is not None

    # ------------------------------------------------------------------
    # get_by_id
    # ------------------------------------------------------------------

    def test_get_by_id_encontrado(self, db, repository, config_data):
        config = repository.create(db, Configuracao(**config_data))
        result = repository.get_by_id(db, config.id)

        assert result is not None
        assert result.id == config.id

    def test_get_by_id_nao_encontrado(self, db, repository):
        result = repository.get_by_id(db, uuid4())
        assert result is None

    # ------------------------------------------------------------------
    # get_by_processo_id (mais recente)
    # ------------------------------------------------------------------

    def test_get_by_processo_id_retorna_mais_recente(
        self, db, repository, config_data, processo
    ):
        """Deve retornar a configuração mais recente."""
        from datetime import datetime, timedelta

        c1 = repository.create(db, Configuracao(**config_data))
        # Força c1 a ter um created_at mais antigo para garantir ordenação
        c1.created_at = datetime.now() - timedelta(seconds=10)
        db.add(c1)
        db.commit()
        db.refresh(c1)

        config_data2 = dict(config_data)
        config_data2["timeout"] = 7200
        c2 = repository.create(db, Configuracao(**config_data2))

        result = repository.get_by_processo_id(db, processo.id)
        assert result is not None
        # A mais recente é c2 (criada por último)
        assert result.id == c2.id
        assert result.timeout == 7200

    def test_get_by_processo_id_nenhuma(self, db, repository):
        result = repository.get_by_processo_id(db, uuid4())
        assert result is None

    # ------------------------------------------------------------------
    # get_all_by_processo_id
    # ------------------------------------------------------------------

    def test_get_all_by_processo_id_retorna_historico(
        self, db, repository, config_data, processo
    ):
        repository.create(db, Configuracao(**config_data))
        repository.create(db, Configuracao(**config_data))

        result = repository.get_all_by_processo_id(db, processo.id)

        assert len(result) == 2

    def test_get_all_by_processo_id_vazio(self, db, repository):
        result = repository.get_all_by_processo_id(db, uuid4())
        assert result == []

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------

    def test_update(self, db, repository, config_data):
        config = repository.create(db, Configuracao(**config_data))
        config.timeout = 9999
        updated = repository.update(db, config)

        assert updated.timeout == 9999

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    def test_delete_encontrado(self, db, repository, config_data):
        config = repository.create(db, Configuracao(**config_data))
        result = repository.delete(db, config.id)

        assert result is True
        assert repository.get_by_id(db, config.id) is None

    def test_delete_nao_encontrado(self, db, repository):
        result = repository.delete(db, uuid4())
        assert result is False
