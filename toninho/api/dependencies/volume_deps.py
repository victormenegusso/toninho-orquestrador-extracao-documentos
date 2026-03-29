"""Dependencies para injeção de VolumeService."""

from toninho.repositories.volume_repository import VolumeRepository
from toninho.services.volume_service import VolumeService


def get_volume_service() -> VolumeService:
    """
    Dependency para obter instância de VolumeService.

    Returns:
        VolumeService configurado com repository
    """
    return VolumeService(repository=VolumeRepository())
