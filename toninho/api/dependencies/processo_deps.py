"""Dependencies para injeção de ProcessoService."""

from toninho.repositories.processo_repository import ProcessoRepository
from toninho.services.processo_service import ProcessoService


def get_processo_service() -> ProcessoService:
    """
    Dependency para obter instância de ProcessoService.

    Returns:
        ProcessoService configurado com repository
    """
    repository = ProcessoRepository()
    return ProcessoService(repository)
