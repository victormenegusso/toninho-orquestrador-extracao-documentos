"""Dependencies para injeção de PaginaExtraidaService."""

from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.pagina_extraida_repository import PaginaExtraidaRepository
from toninho.services.pagina_extraida_service import PaginaExtraidaService


def get_pagina_extraida_service() -> PaginaExtraidaService:
    """
    Dependency para obter instância de PaginaExtraidaService.

    Returns:
        PaginaExtraidaService configurado com repositories
    """
    return PaginaExtraidaService(
        repository=PaginaExtraidaRepository(),
        execucao_repository=ExecucaoRepository(),
    )
