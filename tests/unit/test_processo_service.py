"""Testes para ProcessoService."""

from datetime import datetime
from unittest.mock import Mock, PropertyMock, patch
from uuid import uuid4

import pytest

from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import ExecucaoStatus, ProcessoStatus
from toninho.models.execucao import Execucao
from toninho.models.processo import Processo
from toninho.schemas.processo import ProcessoCreate, ProcessoUpdate
from toninho.services.processo_service import ProcessoService


class TestProcessoService:
    """Testes para ProcessoService."""

    @pytest.fixture
    def mock_repository(self):
        """Fixture com mock do repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Fixture com instância do service."""
        return ProcessoService(mock_repository)

    @pytest.fixture
    def db_mock(self):
        """Fixture com mock da sessão do banco."""
        return Mock()

    def test_create_processo_sucesso(self, service, mock_repository, db_mock):
        """Testa criação de processo com sucesso."""
        # Setup
        processo_create = ProcessoCreate(
            nome="Novo Processo",
            descricao="Descrição teste",
            status=ProcessoStatus.ATIVO,
        )

        mock_repository.exists_by_nome.return_value = False

        processo_mock = Processo(
            nome=processo_create.nome,
            descricao=processo_create.descricao,
            status=processo_create.status,
        )
        processo_mock.id = uuid4()
        processo_mock.created_at = datetime.now()
        processo_mock.updated_at = datetime.now()

        mock_repository.create.return_value = processo_mock

        # Executar
        result = service.create_processo(db_mock, processo_create)

        # Verificar
        assert result.nome == processo_create.nome
        assert result.descricao == processo_create.descricao
        mock_repository.exists_by_nome.assert_called_once_with(
            db_mock, processo_create.nome
        )
        mock_repository.create.assert_called_once()

    def test_create_processo_nome_duplicado(
        self, service, mock_repository, db_mock
    ):
        """Testa criação com nome duplicado."""
        processo_create = ProcessoCreate(
            nome="Processo Duplicado",
            descricao="Teste",
        )

        mock_repository.exists_by_nome.return_value = True

        # Deve lançar exceção
        with pytest.raises(ConflictError) as exc_info:
            service.create_processo(db_mock, processo_create)

        assert "Já existe um processo" in str(exc_info.value)

    def test_get_processo_encontrado(self, service, mock_repository, db_mock):
        """Testa busca de processo existente."""
        processo_id = uuid4()

        processo_mock = Processo(
            nome="Processo Teste",
            descricao="Teste",
            status=ProcessoStatus.ATIVO,
        )
        processo_mock.id = processo_id
        processo_mock.created_at = datetime.now()
        processo_mock.updated_at = datetime.now()

        mock_repository.get_by_id.return_value = processo_mock

        # Executar
        result = service.get_processo(db_mock, processo_id)

        # Verificar
        assert result.id == processo_id
        assert result.nome == "Processo Teste"
        mock_repository.get_by_id.assert_called_once_with(db_mock, processo_id)

    def test_get_processo_nao_encontrado(self, service, mock_repository, db_mock):
        """Testa busca de processo inexistente."""
        processo_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Deve lançar exceção
        with pytest.raises(NotFoundError) as exc_info:
            service.get_processo(db_mock, processo_id)

        assert "não encontrado" in str(exc_info.value)

    def test_get_processo_detail(self, service, mock_repository, db_mock):
        """Testa busca de detalhes completos."""
        processo_id = uuid4()

        # Criar mock do processo
        processo_mock = Mock()
        processo_mock.id = processo_id
        processo_mock.nome = "Processo Teste"
        processo_mock.descricao = None
        processo_mock.status = ProcessoStatus.ATIVO
        processo_mock.created_at = datetime.now()
        processo_mock.updated_at = datetime.now()
        processo_mock.configuracoes = []
        processo_mock.execucoes = []

        mock_repository.get_by_id_with_details.return_value = processo_mock

        # Executar
        result = service.get_processo_detail(db_mock, processo_id)

        # Verificar
        assert result.id == processo_id
        assert result.nome == "Processo Teste"
        assert result.configuracoes == []
        assert result.execucoes_recentes == []
        assert result.total_execucoes == 0

    def test_list_processos_sucesso(self, service, mock_repository, db_mock):
        """Testa listagem de processos."""
        # Setup
        processos_mock = [
            Processo(nome=f"Processo {i}", status=ProcessoStatus.ATIVO)
            for i in range(5)
        ]
        for i, p in enumerate(processos_mock):
            p.id = uuid4()
            p.created_at = datetime.now()
            p.updated_at = datetime.now()

        mock_repository.get_all.return_value = (processos_mock, 5)

        # Executar
        result = service.list_processos(db_mock, page=1, per_page=10)

        # Verificar
        assert len(result.data) == 5
        assert result.meta.total == 5
        assert result.meta.page == 1
        assert result.meta.per_page == 10

    def test_list_processos_parametros_invalidos(
        self, service, mock_repository, db_mock
    ):
        """Testa validação de parâmetros."""
        # Page < 1
        with pytest.raises(ValidationError):
            service.list_processos(db_mock, page=0)

        # Per_page < 1
        with pytest.raises(ValidationError):
            service.list_processos(db_mock, per_page=0)

        # Per_page > 100
        with pytest.raises(ValidationError):
            service.list_processos(db_mock, per_page=101)

    def test_update_processo_sucesso(self, service, mock_repository, db_mock):
        """Testa atualização com sucesso."""
        processo_id = uuid4()

        processo_mock = Processo(
            nome="Nome Original",
            descricao="Descrição original",
            status=ProcessoStatus.ATIVO,
        )
        processo_mock.id = processo_id
        processo_mock.created_at = datetime.now()
        processo_mock.updated_at = datetime.now()

        mock_repository.get_by_id.return_value = processo_mock
        mock_repository.exists_by_nome.return_value = False

        processo_atualizado = Mock()
        processo_atualizado.id = processo_id
        processo_atualizado.nome = "Nome Atualizado"
        processo_atualizado.descricao = "Descrição atualizada"
        processo_atualizado.status = ProcessoStatus.INATIVO
        processo_atualizado.created_at = datetime.now()
        processo_atualizado.updated_at = datetime.now()

        mock_repository.update.return_value = processo_atualizado

        # Executar
        processo_update = ProcessoUpdate(
            nome="Nome Atualizado",
            descricao="Descrição atualizada",
            status=ProcessoStatus.INATIVO,
        )

        result = service.update_processo(db_mock, processo_id, processo_update)

        # Verificar
        assert result.nome == "Nome Atualizado"
        mock_repository.update.assert_called_once()

    def test_update_processo_nao_encontrado(
        self, service, mock_repository, db_mock
    ):
        """Testa atualização de processo inexistente."""
        processo_id = uuid4()
        mock_repository.get_by_id.return_value = None

        processo_update = ProcessoUpdate(nome="Novo Nome")

        with pytest.raises(NotFoundError):
            service.update_processo(db_mock, processo_id, processo_update)

    def test_update_processo_nome_duplicado(
        self, service, mock_repository, db_mock
    ):
        """Testa atualização com nome já existente."""
        processo_id = uuid4()

        processo_mock = Processo(
            nome="Nome Original",
            status=ProcessoStatus.ATIVO,
        )
        processo_mock.id = processo_id
        processo_mock.created_at = datetime.now()
        processo_mock.updated_at = datetime.now()

        mock_repository.get_by_id.return_value = processo_mock
        mock_repository.exists_by_nome.return_value = True

        processo_update = ProcessoUpdate(nome="Nome Existente")

        with pytest.raises(ConflictError):
            service.update_processo(db_mock, processo_id, processo_update)

    def test_update_processo_sem_campos(self, service, mock_repository, db_mock):
        """Testa atualização sem fornecer campos."""
        processo_id = uuid4()

        processo_mock = Processo(
            nome="Nome Original",
            status=ProcessoStatus.ATIVO,
        )
        processo_mock.id = processo_id
        processo_mock.created_at = datetime.now()
        processo_mock.updated_at = datetime.now()

        mock_repository.get_by_id.return_value = processo_mock

        processo_update = ProcessoUpdate()  # Todos campos None

        with pytest.raises(ValidationError) as exc_info:
            service.update_processo(db_mock, processo_id, processo_update)

        assert "Nenhum campo fornecido" in str(exc_info.value)

    def test_delete_processo_sucesso(self, service, mock_repository, db_mock):
        """Testa deleção com sucesso."""
        processo_id = uuid4()

        processo_mock = Processo(
            nome="Processo Teste",
            status=ProcessoStatus.ATIVO,
        )
        processo_mock.id = processo_id
        processo_mock.execucoes = []

        mock_repository.get_by_id_with_details.return_value = processo_mock
        mock_repository.delete.return_value = True

        # Executar
        result = service.delete_processo(db_mock, processo_id)

        # Verificar
        assert result is True
        mock_repository.delete.assert_called_once_with(db_mock, processo_id)

    def test_delete_processo_nao_encontrado(
        self, service, mock_repository, db_mock
    ):
        """Testa deleção de processo inexistente."""
        processo_id = uuid4()
        mock_repository.get_by_id_with_details.return_value = None

        with pytest.raises(NotFoundError):
            service.delete_processo(db_mock, processo_id)

    def test_delete_processo_com_execucoes_em_andamento(
        self, service, mock_repository, db_mock
    ):
        """Testa deleção com execuções em andamento."""
        processo_id = uuid4()

        # Criar mock do processo com execucoes como atributo simples
        processo_mock = Mock()
        processo_mock.id = processo_id
        processo_mock.nome = "Processo Teste"
        processo_mock.status = ProcessoStatus.ATIVO

        # Execução em andamento
        execucao_mock = Mock()
        execucao_mock.status = ExecucaoStatus.EM_EXECUCAO
        processo_mock.execucoes = [execucao_mock]

        mock_repository.get_by_id_with_details.return_value = processo_mock

        with pytest.raises(ConflictError) as exc_info:
            service.delete_processo(db_mock, processo_id)

        assert "em andamento" in str(exc_info.value)

    def test_get_processo_metricas(self, service, mock_repository, db_mock):
        """Testa cálculo de métricas."""
        processo_id = uuid4()

        processo_mock = Processo(
            nome="Processo Teste",
            status=ProcessoStatus.ATIVO,
        )
        processo_mock.id = processo_id

        mock_repository.get_by_id.return_value = processo_mock

        # Mock queries de estatísticas
        exec_stats_mock = Mock()
        exec_stats_mock.total = 10
        exec_stats_mock.sucesso = 8
        exec_stats_mock.falha = 2
        exec_stats_mock.tempo_medio = 120.5
        exec_stats_mock.ultima_execucao = datetime.now()

        # Criar objeto simples para simular resultado da query
        class PaginaStats:
            total_paginas = 100
            total_bytes = 1024000

        pagina_stats_mock = PaginaStats()

        # Contar quantas vezes query foi chamada para diferenciar as queries
        query_call_count = [0]

        # Mock das queries
        def query_side_effect(*args):
            query_call_count[0] += 1
            query_result = Mock()

            if query_call_count[0] == 1:
                # Primeira query (execuções) - tem apenas filter
                filter_mock = Mock()
                filter_mock.first.return_value = exec_stats_mock
                query_result.filter.return_value = filter_mock
            else:
                # Segunda query (páginas) - tem join e filter
                join_mock = Mock()
                filter_mock = Mock()
                filter_mock.first.return_value = pagina_stats_mock
                join_mock.filter.return_value = filter_mock
                query_result.join.return_value = join_mock

            return query_result

        db_mock.query.side_effect = query_side_effect

        # Executar
        result = service.get_processo_metricas(db_mock, processo_id)

        # Verificar
        assert result.processo_id == processo_id
        assert result.total_execucoes == 10
        assert result.execucoes_sucesso == 8
        assert result.execucoes_falha == 2
        assert result.taxa_sucesso == 80.0
        assert result.tempo_medio_execucao_segundos == 120.5
        assert result.total_paginas_extraidas == 100
        assert result.total_bytes_extraidos == 1024000

    def test_get_processo_metricas_processo_nao_encontrado(
        self, service, mock_repository, db_mock
    ):
        """Testa métricas de processo inexistente."""
        processo_id = uuid4()
        mock_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.get_processo_metricas(db_mock, processo_id)
