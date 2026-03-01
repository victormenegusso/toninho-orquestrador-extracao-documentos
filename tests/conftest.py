"""
Configurações do pytest para o projeto Toninho.

Este arquivo contém fixtures compartilhadas e configurações
globais para todos os testes.
"""
from typing import Callable, Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from toninho.models import Base, Execucao, Processo


@pytest.fixture
def sample_fixture() -> str:
    """Fixture de exemplo."""
    return "test"


@pytest.fixture
async def async_sample_fixture() -> str:
    """Fixture assíncrona de exemplo."""
    return "async_test"


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Fixture que fornece uma sessão de banco de dados para testes.

    Usa banco SQLite in-memory e recria o schema para cada teste,
    garantindo isolamento entre testes.

    Yields:
        Session: Sessão do banco de dados
    """
    # Criar engine SQLite in-memory
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)

    # Criar session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    # Criar sessão
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Limpar todas as tabelas
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def processo_factory(db: Session) -> Callable[..., Processo]:
    """
    Factory fixture para criar instâncias de Processo.

    Args:
        db: Sessão do banco de dados

    Returns:
        Callable: Função que cria e retorna um Processo
    """
    counter = {"value": 0}

    def _create_processo(**kwargs) -> Processo:
        counter["value"] += 1
        defaults = {
            "nome": f"Processo Teste {counter['value']}",
            "descricao": "Descrição de teste",
        }
        defaults.update(kwargs)

        processo = Processo(**defaults)
        db.add(processo)
        db.commit()
        db.refresh(processo)
        return processo

    return _create_processo


@pytest.fixture
def execucao_factory(db: Session, processo_factory: Callable) -> Callable[..., Execucao]:
    """
    Factory fixture para criar instâncias de Execucao.

    Args:
        db: Sessão do banco de dados
        processo_factory: Factory de processos

    Returns:
        Callable: Função que cria e retorna uma Execucao
    """
    def _create_execucao(**kwargs) -> Execucao:
        if "processo_id" not in kwargs:
            processo = processo_factory()
            kwargs["processo_id"] = processo.id

        execucao = Execucao(**kwargs)
        db.add(execucao)
        db.commit()
        db.refresh(execucao)
        return execucao

    return _create_execucao
