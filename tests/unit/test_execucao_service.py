"""Testes unitários para ExecucaoService."""

import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import ExecucaoStatus
from toninho.models.execucao import Execucao
from toninho.models.processo import Processo
from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.schemas.execucao import ExecucaoStatusUpdate
from toninho.services.execucao_service import ExecucaoService, validar_transicao

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    return MagicMock(spec=ExecucaoRepository)


@pytest.fixture
def mock_processo_repo():
    return MagicMock(spec=ProcessoRepository)


@pytest.fixture
def service(mock_repo, mock_processo_repo):
    return ExecucaoService(
        repository=mock_repo,
        processo_repository=mock_processo_repo,
    )


@pytest.fixture
def processo_id():
    return uuid4()


@pytest.fixture
def execucao_id():
    return uuid4()


@pytest.fixture
def fake_processo(processo_id):
    p = MagicMock(spec=Processo)
    p.id = processo_id
    return p


def make_fake_execucao(
    execucao_id=None,
    processo_id=None,
    status=ExecucaoStatus.AGUARDANDO,
    paginas=0,
    bytes_extraidos=0,
    taxa_erro=0.0,
):
    e = MagicMock(spec=Execucao)
    e.id = execucao_id or uuid4()
    e.processo_id = processo_id or uuid4()
    e.status = status
    e.paginas_processadas = paginas
    e.bytes_extraidos = bytes_extraidos
    e.taxa_erro = taxa_erro
    e.tentativa_atual = 1
    e.iniciado_em = None
    e.finalizado_em = None
    e.created_at = datetime.datetime.now()
    e.updated_at = datetime.datetime.now()
    return e


# ---------------------------------------------------------------------------
# Testes: validar_transicao
# ---------------------------------------------------------------------------


class TestValidarTransicao:
    def test_criado_para_aguardando(self):
        assert validar_transicao(ExecucaoStatus.CRIADO, ExecucaoStatus.AGUARDANDO)

    def test_aguardando_para_em_execucao(self):
        assert validar_transicao(ExecucaoStatus.AGUARDANDO, ExecucaoStatus.EM_EXECUCAO)

    def test_em_execucao_para_concluido(self):
        assert validar_transicao(ExecucaoStatus.EM_EXECUCAO, ExecucaoStatus.CONCLUIDO)

    def test_em_execucao_para_pausado(self):
        assert validar_transicao(ExecucaoStatus.EM_EXECUCAO, ExecucaoStatus.PAUSADO)

    def test_pausado_para_em_execucao(self):
        assert validar_transicao(ExecucaoStatus.PAUSADO, ExecucaoStatus.EM_EXECUCAO)

    def test_concluido_para_em_execucao_invalido(self):
        assert not validar_transicao(
            ExecucaoStatus.CONCLUIDO, ExecucaoStatus.EM_EXECUCAO
        )

    def test_cancelado_para_aguardando_invalido(self):
        assert not validar_transicao(
            ExecucaoStatus.CANCELADO, ExecucaoStatus.AGUARDANDO
        )

    def test_falhou_para_em_execucao_invalido(self):
        assert not validar_transicao(ExecucaoStatus.FALHOU, ExecucaoStatus.EM_EXECUCAO)

    def test_em_execucao_para_cancelado(self):
        assert validar_transicao(ExecucaoStatus.EM_EXECUCAO, ExecucaoStatus.CANCELADO)

    def test_aguardando_para_cancelado(self):
        assert validar_transicao(ExecucaoStatus.AGUARDANDO, ExecucaoStatus.CANCELADO)


# ---------------------------------------------------------------------------
# Testes: CreateExecucao
# ---------------------------------------------------------------------------


class TestCreateExecucao:
    def test_create_sucesso(
        self, service, mock_repo, mock_processo_repo, fake_processo, processo_id
    ):
        fake_exec = make_fake_execucao(
            processo_id=processo_id, status=ExecucaoStatus.AGUARDANDO
        )
        mock_processo_repo.get_by_id.return_value = fake_processo
        mock_repo.get_em_execucao.return_value = None
        mock_repo.create.return_value = fake_exec
        mock_repo.update.return_value = fake_exec

        result = service.create_execucao(MagicMock(), processo_id)

        assert result.processo_id == processo_id
        mock_repo.create.assert_called_once()

    def test_create_processo_nao_existe(self, service, mock_processo_repo, processo_id):
        mock_processo_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.create_execucao(MagicMock(), processo_id)

    def test_create_bloqueia_segundo_em_execucao(
        self, service, mock_repo, mock_processo_repo, fake_processo, processo_id
    ):
        fake_exec_ativa = make_fake_execucao(
            processo_id=processo_id, status=ExecucaoStatus.EM_EXECUCAO
        )
        mock_processo_repo.get_by_id.return_value = fake_processo
        mock_repo.get_em_execucao.return_value = fake_exec_ativa

        with pytest.raises(ConflictError):
            service.create_execucao(MagicMock(), processo_id)


# ---------------------------------------------------------------------------
# Testes: GetExecucao
# ---------------------------------------------------------------------------


class TestGetExecucao:
    def test_get_sucesso(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(execucao_id=execucao_id)
        mock_repo.get_by_id.return_value = fake_exec

        result = service.get_execucao(MagicMock(), execucao_id)
        assert result.id == execucao_id

    def test_get_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_execucao(MagicMock(), execucao_id)


# ---------------------------------------------------------------------------
# Testes: UpdateExecucaoStatus
# ---------------------------------------------------------------------------


class TestUpdateExecucaoStatus:
    def test_transicao_valida(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.AGUARDANDO
        )
        mock_repo.get_by_id.return_value = fake_exec
        updated = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.EM_EXECUCAO
        )
        mock_repo.update.return_value = updated

        result = service.update_execucao_status(
            MagicMock(),
            execucao_id,
            ExecucaoStatusUpdate(status=ExecucaoStatus.EM_EXECUCAO),
        )
        assert result.status == ExecucaoStatus.EM_EXECUCAO

    def test_transicao_invalida(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.CONCLUIDO
        )
        mock_repo.get_by_id.return_value = fake_exec

        with pytest.raises(ValidationError):
            service.update_execucao_status(
                MagicMock(),
                execucao_id,
                ExecucaoStatusUpdate(status=ExecucaoStatus.EM_EXECUCAO),
            )

    def test_execucao_nao_encontrada(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.update_execucao_status(
                MagicMock(),
                execucao_id,
                ExecucaoStatusUpdate(status=ExecucaoStatus.EM_EXECUCAO),
            )


# ---------------------------------------------------------------------------
# Testes: CancelarExecucao
# ---------------------------------------------------------------------------


class TestCancelarExecucao:
    def test_cancelar_em_execucao(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.EM_EXECUCAO
        )
        cancelled = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.CANCELADO
        )
        mock_repo.get_by_id.return_value = fake_exec
        mock_repo.update.return_value = cancelled

        result = service.cancelar_execucao(MagicMock(), execucao_id)
        assert result.status == ExecucaoStatus.CANCELADO

    def test_cancelar_aguardando(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.AGUARDANDO
        )
        cancelled = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.CANCELADO
        )
        mock_repo.get_by_id.return_value = fake_exec
        mock_repo.update.return_value = cancelled

        result = service.cancelar_execucao(MagicMock(), execucao_id)
        assert result.status == ExecucaoStatus.CANCELADO

    def test_cancelar_ja_concluido(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.CONCLUIDO
        )
        mock_repo.get_by_id.return_value = fake_exec

        with pytest.raises(ConflictError):
            service.cancelar_execucao(MagicMock(), execucao_id)

    def test_cancelar_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.cancelar_execucao(MagicMock(), execucao_id)


# ---------------------------------------------------------------------------
# Testes: PausarExecucao / RetormarExecucao
# ---------------------------------------------------------------------------


class TestPausarRetomar:
    def test_pausar_em_execucao(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.EM_EXECUCAO
        )
        paused = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.PAUSADO
        )
        mock_repo.get_by_id.return_value = fake_exec
        mock_repo.update.return_value = paused

        result = service.pausar_execucao(MagicMock(), execucao_id)
        assert result.status == ExecucaoStatus.PAUSADO

    def test_pausar_ja_pausado_invalido(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.PAUSADO
        )
        mock_repo.get_by_id.return_value = fake_exec

        with pytest.raises(ConflictError):
            service.pausar_execucao(MagicMock(), execucao_id)

    def test_retomar_pausado(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.PAUSADO
        )
        resumed = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.EM_EXECUCAO
        )
        mock_repo.get_by_id.return_value = fake_exec
        mock_repo.update.return_value = resumed

        result = service.retomar_execucao(MagicMock(), execucao_id)
        assert result.status == ExecucaoStatus.EM_EXECUCAO

    def test_retomar_nao_pausado_invalido(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.AGUARDANDO
        )
        mock_repo.get_by_id.return_value = fake_exec

        with pytest.raises(ConflictError):
            service.retomar_execucao(MagicMock(), execucao_id)


# ---------------------------------------------------------------------------
# Testes: GetProgresso
# ---------------------------------------------------------------------------


class TestGetProgresso:
    def test_progresso_zero(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(execucao_id=execucao_id, paginas=0)
        mock_repo.get_by_id.return_value = fake_exec

        result = service.get_progresso(MagicMock(), execucao_id)

        assert result.execucao_id == execucao_id
        assert result.progresso_percentual == 0.0

    def test_progresso_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_progresso(MagicMock(), execucao_id)


# ---------------------------------------------------------------------------
# Testes: GetExecucaoMetricas
# ---------------------------------------------------------------------------


class TestGetExecucaoMetricas:
    def test_metricas_sem_duracao(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, paginas=5, taxa_erro=10.0
        )
        mock_repo.get_by_id.return_value = fake_exec

        result = service.get_execucao_metricas(MagicMock(), execucao_id)

        assert result.execucao_id == execucao_id
        assert result.paginas_processadas == 5
        assert result.taxa_sucesso == 90.0
        assert result.duracao_segundos is None

    def test_metricas_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_execucao_metricas(MagicMock(), execucao_id)


# ---------------------------------------------------------------------------
# Testes: DeleteExecucao
# ---------------------------------------------------------------------------


class TestDeleteExecucao:
    def test_delete_sucesso(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.CONCLUIDO
        )
        mock_repo.get_by_id.return_value = fake_exec
        mock_repo.delete.return_value = True

        result = service.delete_execucao(MagicMock(), execucao_id)
        assert result is True

    def test_delete_em_execucao_bloqueado(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(
            execucao_id=execucao_id, status=ExecucaoStatus.EM_EXECUCAO
        )
        mock_repo.get_by_id.return_value = fake_exec

        with pytest.raises(ConflictError):
            service.delete_execucao(MagicMock(), execucao_id)

    def test_delete_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_execucao(MagicMock(), execucao_id)


# ---------------------------------------------------------------------------
# Testes: GetExecucaoDetail
# ---------------------------------------------------------------------------


class TestGetExecucaoDetail:
    def test_get_detail_sucesso(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(execucao_id=execucao_id)
        mock_repo.get_by_id.return_value = fake_exec

        result = service.get_execucao_detail(MagicMock(), execucao_id)

        assert result.id == execucao_id
        mock_repo.get_by_id.assert_called_once_with(
            mock_repo.get_by_id.call_args[0][0],
            execucao_id,
            with_relations=True,
        )

    def test_get_detail_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_execucao_detail(MagicMock(), execucao_id)

    def test_get_detail_com_duracao(self, service, mock_repo, execucao_id):
        """Testa detalhe quando iniciado_em e finalizado_em estão preenchidos."""
        now = datetime.datetime.now()
        fake_exec = make_fake_execucao(execucao_id=execucao_id, paginas=10)
        fake_exec.iniciado_em = now - datetime.timedelta(seconds=120)
        fake_exec.finalizado_em = now
        mock_repo.get_by_id.return_value = fake_exec

        result = service.get_execucao_detail(MagicMock(), execucao_id)
        assert result.id == execucao_id


# ---------------------------------------------------------------------------
# Testes: ListExecucoes
# ---------------------------------------------------------------------------


class TestListExecucoes:
    def test_list_com_processo_id(self, service, mock_repo, processo_id):
        fake_exec = make_fake_execucao(processo_id=processo_id)
        mock_repo.get_all_by_processo_id.return_value = ([fake_exec], 1)

        result = service.list_execucoes(MagicMock(), processo_id=processo_id)

        assert result.meta.total == 1
        mock_repo.get_all_by_processo_id.assert_called_once()

    def test_list_sem_processo_id(self, service, mock_repo):
        fake_exec = make_fake_execucao()
        mock_repo.get_all.return_value = ([fake_exec], 1)

        result = service.list_execucoes(MagicMock())

        assert result.meta.total == 1
        mock_repo.get_all.assert_called_once()

    def test_list_com_filtro_status(self, service, mock_repo):
        fake_exec = make_fake_execucao(status=ExecucaoStatus.CONCLUIDO)
        mock_repo.get_all.return_value = ([fake_exec], 1)

        result = service.list_execucoes(MagicMock(), status=ExecucaoStatus.CONCLUIDO)
        assert result.meta.total == 1


# ---------------------------------------------------------------------------
# Testes: NotFoundError em pausar/retomar
# ---------------------------------------------------------------------------


class TestPausarRetormarNotFound:
    def test_pausar_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.pausar_execucao(MagicMock(), execucao_id)

    def test_retomar_nao_encontrado(self, service, mock_repo, execucao_id):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.retomar_execucao(MagicMock(), execucao_id)


# ---------------------------------------------------------------------------
# Testes: _calcular_metricas com duração
# ---------------------------------------------------------------------------


class TestCalcularMetricas:
    def test_com_duracao_e_paginas(self):
        from toninho.services.execucao_service import ExecucaoService

        now = datetime.datetime.now()
        execucao = make_fake_execucao(paginas=10, taxa_erro=5.0)
        execucao.iniciado_em = now - datetime.timedelta(seconds=100)
        execucao.finalizado_em = now

        metricas = ExecucaoService._calcular_metricas(execucao)

        assert metricas.duracao_segundos == 100
        assert metricas.tempo_medio_por_pagina_segundos == 10.0
        assert metricas.taxa_sucesso == 95.0

    def test_com_duracao_sem_paginas(self):
        from toninho.services.execucao_service import ExecucaoService

        now = datetime.datetime.now()
        execucao = make_fake_execucao(paginas=0)
        execucao.iniciado_em = now - datetime.timedelta(seconds=50)
        execucao.finalizado_em = now

        metricas = ExecucaoService._calcular_metricas(execucao)

        assert metricas.duracao_segundos == 50
        assert metricas.tempo_medio_por_pagina_segundos is None


# ---------------------------------------------------------------------------
# Testes: _get_total_paginas
# ---------------------------------------------------------------------------


class TestGetTotalPaginas:
    def test_com_configuracao_com_urls(self, service):
        from unittest.mock import MagicMock, patch

        mock_config = MagicMock()
        mock_config.urls = ["https://a.com", "https://b.com"]

        fake_exec = make_fake_execucao()

        with patch(
            "toninho.repositories.configuracao_repository.ConfiguracaoRepository"
        ) as MockRepo:
            instance = MockRepo.return_value
            instance.get_by_processo_id.return_value = mock_config

            total = service._get_total_paginas(MagicMock(), fake_exec)
            assert total == 2

    def test_sem_configuracao(self, service):
        fake_exec = make_fake_execucao()

        with patch(
            "toninho.repositories.configuracao_repository.ConfiguracaoRepository"
        ) as MockRepo:
            instance = MockRepo.return_value
            instance.get_by_processo_id.return_value = None

            total = service._get_total_paginas(MagicMock(), fake_exec)
            assert total == 0

    def test_config_sem_urls(self, service):
        from unittest.mock import MagicMock, patch

        mock_config = MagicMock()
        mock_config.urls = None

        fake_exec = make_fake_execucao()

        with patch(
            "toninho.repositories.configuracao_repository.ConfiguracaoRepository"
        ) as MockRepo:
            instance = MockRepo.return_value
            instance.get_by_processo_id.return_value = mock_config

            total = service._get_total_paginas(MagicMock(), fake_exec)
            assert total == 0

    def test_repo_levanta_excecao(self, service):
        """Cobre o bloco except em _get_total_paginas."""
        fake_exec = make_fake_execucao()

        with patch(
            "toninho.repositories.configuracao_repository.ConfiguracaoRepository",
            side_effect=RuntimeError("DB error"),
        ):
            total = service._get_total_paginas(MagicMock(), fake_exec)
            assert total == 0


# ---------------------------------------------------------------------------
# Testes: _revogar_task
# ---------------------------------------------------------------------------


class TestRevogarTask:
    def test_sem_task_id(self):
        from toninho.services.execucao_service import ExecucaoService

        execucao = make_fake_execucao()
        execucao.celery_task_id = None

        # Não deve lançar exceção
        ExecucaoService._revogar_task(execucao)

    def test_com_task_id_celery_disponivel(self):
        from toninho.services.execucao_service import ExecucaoService

        execucao = make_fake_execucao()
        execucao.celery_task_id = "fake-task-id-123"

        with patch("celery.current_app") as mock_celery:
            ExecucaoService._revogar_task(execucao)
            mock_celery.control.revoke.assert_called_once_with(
                "fake-task-id-123", terminate=True
            )

    def test_com_task_id_celery_indisponivel(self):
        from toninho.services.execucao_service import ExecucaoService

        execucao = make_fake_execucao()
        execucao.celery_task_id = "fake-task-id-456"

        with patch("celery.current_app") as mock_celery:
            mock_celery.control.revoke.side_effect = RuntimeError("Celery offline")
            # Não deve lançar exceção (best-effort)
            ExecucaoService._revogar_task(execucao)


# ---------------------------------------------------------------------------
# Testes: get_progresso com iniciado_em
# ---------------------------------------------------------------------------


class TestGetProgressoComInicio:
    def test_progresso_com_inicio_e_paginas(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(execucao_id=execucao_id, paginas=5)
        fake_exec.iniciado_em = datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(seconds=60)
        mock_repo.get_by_id.return_value = fake_exec

        with patch.object(service, "_get_total_paginas", return_value=10):
            result = service.get_progresso(MagicMock(), execucao_id)

        assert result.progresso_percentual == 50.0
        assert result.tempo_decorrido_segundos is not None
        assert result.tempo_estimado_restante_segundos is not None

    def test_progresso_com_iniciado_sem_timezone(self, service, mock_repo, execucao_id):
        fake_exec = make_fake_execucao(execucao_id=execucao_id, paginas=3)
        fake_exec.iniciado_em = datetime.datetime.now()  # sem timezone
        mock_repo.get_by_id.return_value = fake_exec

        with patch.object(service, "_get_total_paginas", return_value=10):
            result = service.get_progresso(MagicMock(), execucao_id)

        assert result.tempo_decorrido_segundos is not None
