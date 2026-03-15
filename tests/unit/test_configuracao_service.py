"""Testes unitários para ConfiguracaoService."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from toninho.core.exceptions import NotFoundError
from toninho.models.configuracao import Configuracao
from toninho.models.enums import AgendamentoTipo, FormatoSaida, MetodoExtracao
from toninho.models.processo import Processo
from toninho.repositories.configuracao_repository import ConfiguracaoRepository
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.schemas.configuracao import (
    ConfiguracaoCreate,
    ConfiguracaoUpdate,
)
from toninho.services.configuracao_service import ConfiguracaoService


@pytest.fixture
def mock_repo():
    return MagicMock(spec=ConfiguracaoRepository)


@pytest.fixture
def mock_processo_repo():
    return MagicMock(spec=ProcessoRepository)


@pytest.fixture
def service(mock_repo, mock_processo_repo):
    return ConfiguracaoService(
        repository=mock_repo,
        processo_repository=mock_processo_repo,
    )


@pytest.fixture
def processo_id():
    return uuid4()


@pytest.fixture
def config_id():
    return uuid4()


@pytest.fixture
def fake_processo(processo_id):
    p = MagicMock(spec=Processo)
    p.id = processo_id
    p.nome = "Processo Teste"
    return p


@pytest.fixture
def fake_config(config_id, processo_id):
    c = MagicMock(spec=Configuracao)
    c.id = config_id
    c.processo_id = processo_id
    c.urls = ["https://exemplo.com"]
    c.timeout = 3600
    c.max_retries = 3
    c.formato_saida = FormatoSaida.MULTIPLOS_ARQUIVOS
    c.output_dir = "/tmp/output"
    c.agendamento_tipo = AgendamentoTipo.MANUAL
    c.agendamento_cron = None
    c.use_browser = False
    c.metodo_extracao = MetodoExtracao.HTML2TEXT
    c.created_at = __import__("datetime").datetime.now()
    c.updated_at = __import__("datetime").datetime.now()
    return c


@pytest.fixture
def config_create():
    return ConfiguracaoCreate(
        urls=["https://exemplo.com"],
        timeout=3600,
        max_retries=3,
        output_dir="/tmp/output",
        agendamento_tipo=AgendamentoTipo.MANUAL,
    )


class TestCreateConfiguracao:
    def test_create_sucesso(
        self,
        service,
        mock_repo,
        mock_processo_repo,
        fake_processo,
        fake_config,
        processo_id,
        config_create,
    ):
        mock_processo_repo.get_by_id.return_value = fake_processo
        mock_repo.create.return_value = fake_config

        result = service.create_configuracao(MagicMock(), processo_id, config_create)

        assert result.id == fake_config.id
        mock_repo.create.assert_called_once()

    def test_create_processo_nao_existe(
        self, service, mock_processo_repo, processo_id, config_create
    ):
        mock_processo_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.create_configuracao(MagicMock(), processo_id, config_create)

    def test_create_invalida_urls_invalidas(
        self, service, mock_processo_repo, fake_processo, processo_id
    ):
        mock_processo_repo.get_by_id.return_value = fake_processo

        with pytest.raises(Exception):
            ConfiguracaoCreate(
                urls=["nao-e-uma-url"],
                output_dir="/tmp",
                agendamento_tipo=AgendamentoTipo.MANUAL,
            )

    def test_create_urls_duplicadas(
        self, service, mock_processo_repo, fake_processo, processo_id
    ):
        mock_processo_repo.get_by_id.return_value = fake_processo

        with pytest.raises(Exception):
            ConfiguracaoCreate(
                urls=["https://exemplo.com", "https://exemplo.com"],
                output_dir="/tmp",
                agendamento_tipo=AgendamentoTipo.MANUAL,
            )

    def test_create_lista_urls_vazia_invalida(self):
        """Lista vazia deve causar erro de validação Pydantic."""
        with pytest.raises(Exception):
            ConfiguracaoCreate(
                urls=[],
                output_dir="/tmp",
                agendamento_tipo=AgendamentoTipo.MANUAL,
            )

    def test_create_cron_obrigatorio_se_recorrente(
        self, service, mock_processo_repo, fake_processo, processo_id
    ):
        mock_processo_repo.get_by_id.return_value = fake_processo

        with pytest.raises(Exception):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                output_dir="/tmp",
                agendamento_tipo=AgendamentoTipo.RECORRENTE,
                agendamento_cron=None,
            )

    def test_create_timeout_invalido(self):
        """Timeout acima de 86400 deve ser rejeitado."""
        with pytest.raises(Exception):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                timeout=999999,
                output_dir="/tmp",
                agendamento_tipo=AgendamentoTipo.MANUAL,
            )

    def test_create_max_retries_invalido(self):
        """max_retries > 10 deve ser rejeitado."""
        with pytest.raises(Exception):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                max_retries=99,
                output_dir="/tmp",
                agendamento_tipo=AgendamentoTipo.MANUAL,
            )


class TestGetConfiguracao:
    def test_get_sucesso(self, service, mock_repo, fake_config, config_id):
        mock_repo.get_by_id.return_value = fake_config

        result = service.get_configuracao(MagicMock(), config_id)
        assert result.id == fake_config.id

    def test_get_nao_encontrado(self, service, mock_repo, config_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_configuracao(MagicMock(), config_id)


class TestGetConfiguracaoByProcesso:
    def test_retorna_mais_recente(
        self,
        service,
        mock_repo,
        mock_processo_repo,
        fake_processo,
        fake_config,
        processo_id,
    ):
        mock_processo_repo.get_by_id.return_value = fake_processo
        mock_repo.get_by_processo_id.return_value = fake_config

        result = service.get_configuracao_by_processo(MagicMock(), processo_id)
        assert result.id == fake_config.id

    def test_processo_sem_configuracao(
        self, service, mock_repo, mock_processo_repo, fake_processo, processo_id
    ):
        mock_processo_repo.get_by_id.return_value = fake_processo
        mock_repo.get_by_processo_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_configuracao_by_processo(MagicMock(), processo_id)

    def test_processo_nao_existe(self, service, mock_processo_repo, processo_id):
        mock_processo_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_configuracao_by_processo(MagicMock(), processo_id)


class TestListConfiguracoesByProcesso:
    def test_lista_historico(
        self,
        service,
        mock_repo,
        mock_processo_repo,
        fake_processo,
        fake_config,
        processo_id,
    ):
        mock_processo_repo.get_by_id.return_value = fake_processo
        mock_repo.get_all_by_processo_id.return_value = [fake_config, fake_config]

        result = service.list_configuracoes_by_processo(MagicMock(), processo_id)
        assert len(result) == 2

    def test_processo_nao_existe(self, service, mock_processo_repo, processo_id):
        mock_processo_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.list_configuracoes_by_processo(MagicMock(), processo_id)


class TestUpdateConfiguracao:
    def test_update_sucesso(self, service, mock_repo, fake_config, config_id):
        mock_repo.get_by_id.return_value = fake_config
        mock_repo.update.return_value = fake_config

        result = service.update_configuracao(
            MagicMock(),
            config_id,
            ConfiguracaoUpdate(timeout=7200),
        )
        assert result is not None

    def test_update_nao_encontrado(self, service, mock_repo, config_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.update_configuracao(
                MagicMock(), config_id, ConfiguracaoUpdate(timeout=7200)
            )


class TestDeleteConfiguracao:
    def test_delete_sucesso(self, service, mock_repo, fake_config, config_id):
        mock_repo.get_by_id.return_value = fake_config
        mock_repo.delete.return_value = True

        result = service.delete_configuracao(MagicMock(), config_id)
        assert result is True

    def test_delete_nao_encontrado(self, service, mock_repo, config_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_configuracao(MagicMock(), config_id)


class TestValidarAgendamento:
    def test_expressao_valida(self, service):
        info = service.validar_agendamento("0 2 * * *")
        assert info.valida is True
        assert len(info.proximas_execucoes) == 5
        assert "Diariamente" in info.descricao_legivel

    def test_expressao_invalida(self, service):
        info = service.validar_agendamento("invalid")
        assert info.valida is False
        assert info.proximas_execucoes == []

    def test_expressao_cron_a_cada_15_min(self, service):
        info = service.validar_agendamento("*/15 * * * *")
        assert info.valida is True
        assert "15" in info.descricao_legivel

    def test_expressao_4_campos_invalida(self, service):
        info = service.validar_agendamento("0 2 * *")
        assert info.valida is False

    def test_expressao_dias_uteis(self, service):
        info = service.validar_agendamento("0 2 * * 1-5")
        assert info.valida is True

    def test_expressao_primeiro_dia_mes(self, service):
        info = service.validar_agendamento("0 0 1 * *")
        assert info.valida is True
