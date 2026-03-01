"""
Response wrappers padrão para APIs.

Define estruturas de resposta consistentes para sucesso, listas e erros.
"""
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from toninho.schemas.base import BaseSchema

# TypeVar para generic responses
T = TypeVar("T")


class SuccessResponse(BaseSchema, Generic[T]):
    """
    Wrapper padrão para respostas de sucesso.

    Encapsula dados de resposta em um campo 'data' consistente.

    Attributes:
        data: Dados da resposta (tipo genérico)

    Example:
        ```python
        response = SuccessResponse[ProcessoResponse](data=processo)
        # { "data": { "id": "...", "nome": "..." } }
        ```
    """

    data: T = Field(..., description="Dados da resposta")


class PaginationMeta(BaseSchema):
    """
    Metadados de paginação para respostas de listas.

    Attributes:
        page: Página atual (1-based)
        per_page: Itens por página
        total: Total de itens disponíveis
        total_pages: Total de páginas
    """

    page: int = Field(..., ge=1, description="Página atual")
    per_page: int = Field(..., ge=1, le=100, description="Itens por página")
    total: int = Field(..., ge=0, description="Total de itens")
    total_pages: int = Field(..., ge=0, description="Total de páginas")


class SuccessListResponse(BaseSchema, Generic[T]):
    """
    Wrapper padrão para respostas de listas paginadas.

    Encapsula lista de dados e metadados de paginação.

    Attributes:
        data: Lista de itens
        meta: Metadados de paginação

    Example:
        ```python
        response = SuccessListResponse[ProcessoSummary](
            data=[processo1, processo2],
            meta=PaginationMeta(page=1, per_page=10, total=2, total_pages=1)
        )
        ```
    """

    data: List[T] = Field(..., description="Lista de itens")
    meta: PaginationMeta = Field(..., description="Metadados de paginação")


class ErrorDetail(BaseSchema):
    """
    Detalhe de um erro específico.

    Attributes:
        field: Campo que causou o erro (opcional)
        message: Mensagem descritiva do erro

    Example:
        ```python
        ErrorDetail(field="nome", message="Nome é obrigatório")
        ```
    """

    field: Optional[str] = Field(None, description="Campo que causou o erro")
    message: str = Field(..., description="Mensagem descritiva do erro")


class ErrorInfo(BaseSchema):
    """
    Informações do erro.

    Attributes:
        code: Código do erro (ex: "VALIDATION_ERROR", "NOT_FOUND")
        message: Mensagem principal do erro
        details: Lista de detalhes adicionais (opcional)
    """

    code: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem principal do erro")
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="Detalhes adicionais do erro"
    )


class ErrorResponse(BaseSchema):
    """
    Wrapper padrão para respostas de erro.

    Fornece estrutura consistente para comunicar erros ao cliente.

    Attributes:
        error: Informações do erro

    Example:
        ```python
        ErrorResponse(
            error=ErrorInfo(
                code="NOT_FOUND",
                message="Processo não encontrado",
                details=[ErrorDetail(field="id", message="ID inválido")]
            )
        )
        ```
    """

    error: ErrorInfo = Field(..., description="Informações do erro")


# Helpers para criar responses facilmente

def success_response(data: T) -> SuccessResponse[T]:
    """
    Helper para criar SuccessResponse.

    Args:
        data: Dados a serem encapsulados

    Returns:
        SuccessResponse: Response wrapper com dados
    """
    return SuccessResponse(data=data)


def success_list_response(
    data: List[T],
    page: int,
    per_page: int,
    total: int,
) -> SuccessListResponse[T]:
    """
    Helper para criar SuccessListResponse.

    Args:
        data: Lista de itens
        page: Página atual
        per_page: Itens por página
        total: Total de itens

    Returns:
        SuccessListResponse: Response wrapper com lista e paginação
    """
    total_pages = (total + per_page - 1) // per_page  # ceil division

    return SuccessListResponse(
        data=data,
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        )
    )


def error_response(
    code: str,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
) -> ErrorResponse:
    """
    Helper para criar ErrorResponse.

    Args:
        code: Código do erro
        message: Mensagem do erro
        details: Detalhes adicionais (opcional)

    Returns:
        ErrorResponse: Response wrapper com erro
    """
    return ErrorResponse(
        error=ErrorInfo(
            code=code,
            message=message,
            details=details,
        )
    )
