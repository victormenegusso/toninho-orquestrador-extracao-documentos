"""Dependencies para injeção de ConfiguracaoService."""

from toninho.repositories.configuracao_repository import ConfiguracaoRepository
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.services.configuracao_service import ConfiguracaoService


def get_configuracao_service() -> ConfiguracaoService:
    """
    Dependency para obter instância de ConfiguracaoService.

    Returns:
        ConfiguracaoService configurado com repositories
    """
    return ConfiguracaoService(
        repository=ConfiguracaoRepository(),
        processo_repository=ProcessoRepository(),
    )
