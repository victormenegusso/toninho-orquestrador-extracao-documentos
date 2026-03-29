"""
Models do Toninho.

Este módulo exporta todos os models e enums para fácil importação.
"""

from toninho.models.base import Base, TimestampMixin, UUIDMixin
from toninho.models.configuracao import Configuracao
from toninho.models.enums import (
    AgendamentoTipo,
    ExecucaoStatus,
    FormatoSaida,
    LogNivel,
    PaginaStatus,
    ProcessoStatus,
    VolumeStatus,
    VolumeTipo,
)
from toninho.models.execucao import Execucao
from toninho.models.log import Log
from toninho.models.pagina_extraida import PaginaExtraida
from toninho.models.processo import Processo
from toninho.models.volume import Volume

__all__ = [
    # Base
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    # Models
    "Processo",
    "Configuracao",
    "Execucao",
    "Log",
    "PaginaExtraida",
    "Volume",
    # Enums
    "ProcessoStatus",
    "FormatoSaida",
    "AgendamentoTipo",
    "ExecucaoStatus",
    "LogNivel",
    "PaginaStatus",
    "VolumeStatus",
    "VolumeTipo",
]
