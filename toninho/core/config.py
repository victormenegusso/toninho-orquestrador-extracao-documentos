"""
Configurações da aplicação Toninho.

Este módulo utiliza Pydantic Settings para gerenciar variáveis
de ambiente e configurações da aplicação.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    # Servidor
    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SQL_ECHO: bool = False  # Log de queries SQL — False por padrao para nao poluir logs

    # Banco de Dados
    DATABASE_URL: str = "sqlite:///./toninho.db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Workers
    MAX_CONCURRENT_PROCESSES: int = 5
    WORKER_CONCURRENCY: int = 2

    # Extração
    DEFAULT_TIMEOUT: int = 3600
    MAX_RETRIES: int = 3
    MAX_SIZE_PER_EXTRACTION: int = 1073741824  # 1GB
    OUTPUT_DIR: str = "./output"

    # Cache
    CACHE_HTTP_REQUESTS: bool = True
    CACHE_EXPIRATION: int = 3600

    # Processamento
    PARALLEL_THREADS: int = 4

    # Storage
    STORAGE_TYPE: str = "local"

    # Segurança
    SECRET_KEY: str = "change-me-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Retorna instância singleton das configurações."""
    return Settings()


settings = get_settings()
