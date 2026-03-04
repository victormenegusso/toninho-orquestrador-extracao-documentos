"""
Configuração do banco de dados e gerenciamento de sessões.

Este módulo configura o SQLAlchemy engine, SessionLocal e
fornece a dependency para injeção de sessão no FastAPI.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from toninho.core.config import settings
from toninho.models.base import Base

# Configurar engine SQLite com parâmetros otimizados
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessário para FastAPI com SQLite
    pool_pre_ping=True,  # Detectar conexões fechadas
    echo=settings.SQL_ECHO,  # Log queries SQL (controlado por SQL_ECHO, nao por DEBUG)
)


# Event listener para habilitar foreign keys no SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Habilita foreign key constraints no SQLite.

    SQLite desabilita foreign keys por default. Este listener
    garante que elas estejam habilitadas em todas as conexões.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Configurar SessionLocal para criação de sessões
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Objetos usáveis após commit
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para injetar sessão de banco de dados no FastAPI.

    Uso:
        @app.get("/processos")
        def list_processos(db: Session = Depends(get_db)):
            return db.query(Processo).all()

    A sessão é automaticamente fechada após a requisição,
    mesmo em caso de erro.

    Yields:
        Session: Sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa o banco de dados criando todas as tabelas.

    Esta função deve ser usada apenas em desenvolvimento/testes.
    Em produção, use Alembic migrations.

    Nota:
        Não deleta tabelas existentes, apenas cria as que não existem.
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Remove todas as tabelas do banco de dados.

    ATENÇÃO: Esta função é DESTRUTIVA e apaga todos os dados.
    Use apenas em desenvolvimento/testes.
    """
    Base.metadata.drop_all(bind=engine)
