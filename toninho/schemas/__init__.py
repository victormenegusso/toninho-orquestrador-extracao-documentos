"""
Schemas Pydantic do Toninho.

Este módulo exporta todos os schemas para fácil importação.
"""

# Base
from toninho.schemas.base import BaseSchema

# Configuracao
from toninho.schemas.configuracao import (
    ConfiguracaoCreate,
    ConfiguracaoResponse,
    ConfiguracaoUpdate,
)

# Execucao
from toninho.schemas.execucao import (
    ExecucaoCreate,
    ExecucaoResponse,
    ExecucaoStatusUpdate,
    ExecucaoSummary,
    ExecucaoUpdate,
)

# Log
from toninho.schemas.log import (
    LogCreate,
    LogFilter,
    LogResponse,
    LogSummary,
)

# Pagina Extraida
from toninho.schemas.pagina_extraida import (
    PaginaExtraidaCreate,
    PaginaExtraidaDetail,
    PaginaExtraidaResponse,
    PaginaExtraidaSummary,
)

# Processo
from toninho.schemas.processo import (
    ProcessoCreate,
    ProcessoDetail,
    ProcessoMetricas,
    ProcessoResponse,
    ProcessoSummary,
    ProcessoUpdate,
)

# Responses
from toninho.schemas.responses import (
    ErrorDetail,
    ErrorInfo,
    ErrorResponse,
    PaginationMeta,
    SuccessListResponse,
    SuccessResponse,
    error_response,
    success_list_response,
    success_response,
)

# Validators
from toninho.schemas.validators import (
    validate_cron_expression,
    validate_path,
    validate_timeout,
    validate_url,
    validate_urls_list,
)

# Volume
from toninho.schemas.volume import (
    VolumeCreate,
    VolumeResponse,
    VolumeSummary,
    VolumeUpdate,
    VolumeValidationResult,
)

__all__ = [
    # Base
    "BaseSchema",
    # Responses
    "SuccessResponse",
    "SuccessListResponse",
    "PaginationMeta",
    "ErrorResponse",
    "ErrorInfo",
    "ErrorDetail",
    "success_response",
    "success_list_response",
    "error_response",
    # Validators
    "validate_url",
    "validate_urls_list",
    "validate_cron_expression",
    "validate_path",
    "validate_timeout",
    # Processo
    "ProcessoCreate",
    "ProcessoUpdate",
    "ProcessoResponse",
    "ProcessoSummary",
    "ProcessoDetail",
    "ProcessoMetricas",
    # Configuracao
    "ConfiguracaoCreate",
    "ConfiguracaoUpdate",
    "ConfiguracaoResponse",
    # Execucao
    "ExecucaoCreate",
    "ExecucaoUpdate",
    "ExecucaoResponse",
    "ExecucaoSummary",
    "ExecucaoStatusUpdate",
    # Log
    "LogCreate",
    "LogResponse",
    "LogSummary",
    "LogFilter",
    # Pagina Extraida
    "PaginaExtraidaCreate",
    "PaginaExtraidaResponse",
    "PaginaExtraidaSummary",
    "PaginaExtraidaDetail",
    # Volume
    "VolumeCreate",
    "VolumeUpdate",
    "VolumeResponse",
    "VolumeSummary",
    "VolumeValidationResult",
]

# Rebuild models with forward references
ProcessoDetail.model_rebuild()
