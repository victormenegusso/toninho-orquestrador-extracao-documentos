"""Dependencies para injeção de ExecucaoService."""

from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.services.execucao_service import ExecucaoService


def get_execucao_service() -> ExecucaoService:
    """
    Dependency para obter instância de ExecucaoService.

    Returns:
        ExecucaoService configurado com repositories
    """
    return ExecucaoService(
        repository=ExecucaoRepository(),
        processo_repository=ProcessoRepository(),
    )
