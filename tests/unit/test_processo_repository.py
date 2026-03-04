"""Testes para ProcessoRepository."""

from uuid import uuid4

import pytest

from toninho.models.enums import ProcessoStatus
from toninho.models.processo import Processo
from toninho.repositories.processo_repository import ProcessoRepository


class TestProcessoRepository:
    """Testes para ProcessoRepository."""

    @pytest.fixture
    def repository(self):
        """Fixture que retorna instância do repository."""
        return ProcessoRepository()

    @pytest.fixture
    def processo_data(self):
        """Fixture com dados básicos de processo."""
        return {
            "nome": "Processo Teste",
            "descricao": "Descrição de teste",
            "status": ProcessoStatus.ATIVO,
        }

    def test_create_processo(self, db, repository, processo_data):
        """Testa criação de processo."""
        processo = Processo(**processo_data)

        result = repository.create(db, processo)

        assert result.id is not None
        assert result.nome == processo_data["nome"]
        assert result.descricao == processo_data["descricao"]
        assert result.status == processo_data["status"]
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_get_by_id_encontrado(self, db, repository, processo_data):
        """Testa busca por ID quando processo existe."""
        # Criar processo
        processo = Processo(**processo_data)
        processo = repository.create(db, processo)

        # Buscar
        result = repository.get_by_id(db, processo.id)

        assert result is not None
        assert result.id == processo.id
        assert result.nome == processo.nome

    def test_get_by_id_nao_encontrado(self, db, repository):
        """Testa busca por ID quando processo não existe."""
        fake_id = uuid4()

        result = repository.get_by_id(db, fake_id)

        assert result is None

    def test_get_by_nome_encontrado(self, db, repository, processo_data):
        """Testa busca por nome quando processo existe."""
        # Criar processo
        processo = Processo(**processo_data)
        processo = repository.create(db, processo)

        # Buscar
        result = repository.get_by_nome(db, processo_data["nome"])

        assert result is not None
        assert result.nome == processo_data["nome"]

    def test_get_by_nome_nao_encontrado(self, db, repository):
        """Testa busca por nome quando processo não existe."""
        result = repository.get_by_nome(db, "Nome Inexistente")

        assert result is None

    def test_get_all_sem_filtros(self, db, repository):
        """Testa listagem sem filtros."""
        # Criar múltiplos processos
        for i in range(5):
            processo = Processo(
                nome=f"Processo {i}",
                descricao=f"Descrição {i}",
                status=ProcessoStatus.ATIVO,
            )
            repository.create(db, processo)

        # Listar
        processos, total = repository.get_all(db)

        assert len(processos) == 5
        assert total == 5

    def test_get_all_com_paginacao(self, db, repository):
        """Testa paginação."""
        # Criar 10 processos
        for i in range(10):
            processo = Processo(
                nome=f"Processo {i}",
                descricao=f"Descrição {i}",
                status=ProcessoStatus.ATIVO,
            )
            repository.create(db, processo)

        # Buscar primeira página
        processos_pag1, total = repository.get_all(db, skip=0, limit=5)
        assert len(processos_pag1) == 5
        assert total == 10

        # Buscar segunda página
        processos_pag2, total = repository.get_all(db, skip=5, limit=5)
        assert len(processos_pag2) == 5
        assert total == 10

        # Páginas diferentes
        assert processos_pag1[0].id != processos_pag2[0].id

    def test_get_all_filtro_status(self, db, repository):
        """Testa filtro por status."""
        # Criar processos com status diferentes
        for i in range(3):
            processo = Processo(
                nome=f"Ativo {i}",
                status=ProcessoStatus.ATIVO,
            )
            repository.create(db, processo)

        for i in range(2):
            processo = Processo(
                nome=f"Inativo {i}",
                status=ProcessoStatus.INATIVO,
            )
            repository.create(db, processo)

        # Filtrar por ATIVO
        ativos, total_ativos = repository.get_all(db, status=ProcessoStatus.ATIVO)
        assert len(ativos) == 3
        assert total_ativos == 3

        # Filtrar por INATIVO
        inativos, total_inativos = repository.get_all(db, status=ProcessoStatus.INATIVO)
        assert len(inativos) == 2
        assert total_inativos == 2

    def test_get_all_busca_por_nome(self, db, repository):
        """Testa busca por nome (LIKE)."""
        # Criar processos
        processo1 = Processo(nome="Processo ABC", status=ProcessoStatus.ATIVO)
        processo2 = Processo(nome="Processo XYZ", status=ProcessoStatus.ATIVO)
        processo3 = Processo(nome="Outro Nome", status=ProcessoStatus.ATIVO)

        repository.create(db, processo1)
        repository.create(db, processo2)
        repository.create(db, processo3)

        # Buscar por "Processo"
        resultados, total = repository.get_all(db, busca="Processo")
        assert len(resultados) == 2
        assert total == 2

        # Buscar por "ABC"
        resultados, total = repository.get_all(db, busca="ABC")
        assert len(resultados) == 1
        assert total == 1
        assert resultados[0].nome == "Processo ABC"

    def test_get_all_ordenacao(self, db, repository):
        """Testa ordenação."""
        # Criar processos
        p1 = Processo(nome="B Processo", status=ProcessoStatus.ATIVO)
        p2 = Processo(nome="A Processo", status=ProcessoStatus.ATIVO)
        p3 = Processo(nome="C Processo", status=ProcessoStatus.ATIVO)

        repository.create(db, p1)
        repository.create(db, p2)
        repository.create(db, p3)

        # Ordenar por nome ASC
        processos, _ = repository.get_all(db, order_by="nome", order_dir="asc")
        assert processos[0].nome == "A Processo"
        assert processos[1].nome == "B Processo"
        assert processos[2].nome == "C Processo"

        # Ordenar por nome DESC
        processos, _ = repository.get_all(db, order_by="nome", order_dir="desc")
        assert processos[0].nome == "C Processo"
        assert processos[1].nome == "B Processo"
        assert processos[2].nome == "A Processo"

    def test_update_processo(self, db, repository, processo_data):
        """Testa atualização de processo."""
        # Criar processo
        processo = Processo(**processo_data)
        processo = repository.create(db, processo)

        # Atualizar
        processo.nome = "Nome Atualizado"
        processo.status = ProcessoStatus.INATIVO

        result = repository.update(db, processo)

        assert result.nome == "Nome Atualizado"
        assert result.status == ProcessoStatus.INATIVO

        # Verificar no banco
        db_processo = repository.get_by_id(db, processo.id)
        assert db_processo.nome == "Nome Atualizado"

    def test_delete_processo_sucesso(self, db, repository, processo_data):
        """Testa deleção quando processo existe."""
        # Criar processo
        processo = Processo(**processo_data)
        processo = repository.create(db, processo)

        # Deletar
        result = repository.delete(db, processo.id)

        assert result is True

        # Verificar que foi deletado
        db_processo = repository.get_by_id(db, processo.id)
        assert db_processo is None

    def test_delete_processo_nao_encontrado(self, db, repository):
        """Testa deleção quando processo não existe."""
        fake_id = uuid4()

        result = repository.delete(db, fake_id)

        assert result is False

    def test_exists_by_nome_existe(self, db, repository, processo_data):
        """Testa verificação de existência quando processo existe."""
        # Criar processo
        processo = Processo(**processo_data)
        repository.create(db, processo)

        # Verificar
        result = repository.exists_by_nome(db, processo_data["nome"])

        assert result is True

    def test_exists_by_nome_nao_existe(self, db, repository):
        """Testa verificação de existência quando processo não existe."""
        result = repository.exists_by_nome(db, "Nome Inexistente")

        assert result is False

    def test_exists_by_nome_com_exclude_id(self, db, repository):
        """Testa verificação excluindo o próprio ID (para updates)."""
        # Criar dois processos
        p1 = Processo(nome="Processo 1", status=ProcessoStatus.ATIVO)
        p2 = Processo(nome="Processo 2", status=ProcessoStatus.ATIVO)

        p1 = repository.create(db, p1)
        p2 = repository.create(db, p2)

        # Verificar "Processo 1" excluindo p1.id (deve retornar False)
        result = repository.exists_by_nome(db, "Processo 1", exclude_id=p1.id)
        assert result is False

        # Verificar "Processo 1" excluindo p2.id (deve retornar True)
        result = repository.exists_by_nome(db, "Processo 1", exclude_id=p2.id)
        assert result is True

    def test_count_total(self, db, repository):
        """Testa contagem total de processos."""
        # Criar processos
        for i in range(7):
            processo = Processo(
                nome=f"Processo {i}",
                status=ProcessoStatus.ATIVO,
            )
            repository.create(db, processo)

        # Contar
        total = repository.count_total(db)

        assert total == 7

    def test_count_by_status(self, db, repository):
        """Testa contagem por status."""
        # Criar processos com status diferentes
        for i in range(3):
            processo = Processo(
                nome=f"Ativo {i}",
                status=ProcessoStatus.ATIVO,
            )
            repository.create(db, processo)

        for i in range(2):
            processo = Processo(
                nome=f"Inativo {i}",
                status=ProcessoStatus.INATIVO,
            )
            repository.create(db, processo)

        # Contar
        count_ativo = repository.count_by_status(db, ProcessoStatus.ATIVO)
        count_inativo = repository.count_by_status(db, ProcessoStatus.INATIVO)

        assert count_ativo == 3
        assert count_inativo == 2

    def test_get_by_id_with_details(self, db, repository, processo_factory):
        """Testa busca com eager loading de relacionamentos."""
        # Criar processo com configurações e execuções
        processo = processo_factory()

        # Buscar com detalhes
        result = repository.get_by_id_with_details(db, processo.id)

        assert result is not None
        assert result.id == processo.id
        # Relacionamentos devem estar carregados (não lazy)
        assert hasattr(result, "configuracoes")
        assert hasattr(result, "execucoes")
