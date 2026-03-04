"""
Configurações do pytest para o projeto Toninho.

Este arquivo contém fixtures compartilhadas e configurações
globais para todos os testes.
"""

import tempfile
from collections.abc import Callable, Generator
from pathlib import Path

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
def test_engine():
    """
    Fixture que fornece um engine de banco de dados para testes.

    Usa arquivo temporário em vez de in-memory para permitir múltiplas
    conexões (necessário para TestClient do FastAPI).
    """
    import os

    # Criar arquivo temporário para o banco
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=None,
    )

    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)

    yield engine

    # Limpar
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

    # Remover arquivo temporário
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def db(test_engine) -> Generator[Session, None, None]:
    """
    Fixture que fornece uma sessão de banco de dados para testes.

    Usa o engine compartilhado para garantir que TestClient e testes
    usem o mesmo banco de dados.

    Yields:
        Session: Sessão do banco de dados
    """
    # Criar session factory usando o engine compartilhado
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    # Criar sessão
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


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
def execucao_factory(
    db: Session, processo_factory: Callable
) -> Callable[..., Execucao]:
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


# ─── Additional fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def sample_html() -> bytes:
    """HTML de exemplo para testes de extração."""
    return b"""<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <h1>Main Heading</h1>
    <p>This is a test paragraph.</p>
    <a href="https://example.com/link">Example Link</a>
</body>
</html>"""


@pytest.fixture
def sample_html_file() -> Path:
    """Caminho para arquivo HTML de exemplo nos fixtures."""
    return Path(__file__).parent / "fixtures" / "sample_pages" / "example.html"


@pytest.fixture
def sample_markdown() -> str:
    """Markdown de exemplo para testes."""
    return """# Main Heading

This is a test paragraph.

[Example Link](https://example.com/link)
"""


@pytest.fixture
def mock_storage(tmp_path):
    """LocalFileSystemStorage usando diretório temporário."""
    from toninho.extraction.storage import LocalFileSystemStorage

    return LocalFileSystemStorage(base_dir=str(tmp_path))


@pytest.fixture
def mock_celery_task(mocker):
    """Mock para evitar execução real de tasks Celery."""
    mock = mocker.patch(
        "toninho.workers.tasks.execucao_task.executar_processo_task.delay"
    )
    mock.return_value.id = "test-task-id-123"
    return mock
