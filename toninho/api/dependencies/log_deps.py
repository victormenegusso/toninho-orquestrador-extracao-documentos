"""Dependencies para injeção de LogService."""

from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.log_repository import LogRepository
from toninho.services.log_service import LogService


def get_log_service() -> LogService:
    """
    Dependency para obter instância de LogService.

    Returns:
        LogService configurado com repositories
    """
    return LogService(
        repository=LogRepository(),
        execucao_repository=ExecucaoRepository(),
    )
