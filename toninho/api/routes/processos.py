"""Rotas da API para gerenciamento de Processos."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from toninho.api.dependencies.processo_deps import get_processo_service
from toninho.core.database import get_db
from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import ProcessoStatus
from toninho.schemas.processo import (
    ProcessoCreate,
    ProcessoDetail,
    ProcessoMetricas,
    ProcessoResponse,
    ProcessoSummary,
    ProcessoUpdate,
)
from toninho.schemas.responses import (
    ErrorResponse,
    SuccessListResponse,
    SuccessResponse,
    error_response,
    success_response,
)
from toninho.services.processo_service import ProcessoService

router = APIRouter(prefix="/api/v1/processos", tags=["Processos"])


@router.post(
    "",
    response_model=SuccessResponse[ProcessoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo processo",
    description="Cria um novo processo de extração com os dados fornecidos.",
    responses={
        201: {"description": "Processo criado com sucesso"},
        409: {"description": "Conflito - nome duplicado", "model": ErrorResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def create_processo(
    processo_create: ProcessoCreate,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
) -> SuccessResponse[ProcessoResponse]:
    """
    Cria um novo processo.

    Args:
        processo_create: Dados do processo a ser criado
        db: Sessão do banco de dados
        service: Service de processo

    Returns:
        SuccessResponse com ProcessoResponse

    Raises:
        HTTPException 409: Se nome duplicado
        HTTPException 400: Se dados inválidos
    """
    try:
        processo = service.create_processo(db, processo_create)
        return success_response(data=processo)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Violação de integridade de dados",
        )


@router.get(
    "",
    response_model=SuccessListResponse[ProcessoSummary],
    status_code=status.HTTP_200_OK,
    summary="Listar processos",
    description="Lista processos com paginação e filtros opcionais.",
    responses={
        200: {"description": "Lista de processos"},
        400: {"description": "Parâmetros inválidos", "model": ErrorResponse},
    },
)
def list_processos(
    page: int = Query(1, ge=1, description="Número da página (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Registros por página"),
    status: Optional[ProcessoStatus] = Query(None, description="Filtrar por status"),
    busca: Optional[str] = Query(None, description="Buscar por nome"),
    order_by: str = Query("created_at", description="Campo para ordenação"),
    order_dir: str = Query(
        "desc", pattern="^(asc|desc)$", description="Direção da ordenação"
    ),
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
) -> SuccessListResponse[ProcessoSummary]:
    """
    Lista processos com paginação.

    Args:
        page: Número da página
        per_page: Registros por página
        status: Filtro por status (opcional)
        busca: Busca por nome (opcional)
        order_by: Campo para ordenação
        order_dir: Direção da ordenação
        db: Sessão do banco de dados
        service: Service de processo

    Returns:
        SuccessListResponse com lista de ProcessoSummary

    Raises:
        HTTPException 400: Se parâmetros inválidos
    """
    try:
        return service.list_processos(
            db=db,
            page=page,
            per_page=per_page,
            status=status,
            busca=busca,
            order_by=order_by,
            order_dir=order_dir,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{processo_id}",
    response_model=SuccessResponse[ProcessoResponse],
    status_code=status.HTTP_200_OK,
    summary="Obter processo",
    description="Retorna os dados de um processo específico.",
    responses={
        200: {"description": "Processo encontrado"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
    },
)
def get_processo(
    processo_id: UUID,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
) -> SuccessResponse[ProcessoResponse]:
    """
    Obtém um processo por ID.

    Args:
        processo_id: UUID do processo
        db: Sessão do banco de dados
        service: Service de processo

    Returns:
        SuccessResponse com ProcessoResponse

    Raises:
        HTTPException 404: Se processo não encontrado
    """
    try:
        processo = service.get_processo(db, processo_id)
        return success_response(data=processo)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{processo_id}/detalhes",
    response_model=SuccessResponse[ProcessoDetail],
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes completos do processo",
    description="Retorna processo com configurações e execuções recentes.",
    responses={
        200: {"description": "Detalhes do processo"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
    },
)
def get_processo_detail(
    processo_id: UUID,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
) -> SuccessResponse[ProcessoDetail]:
    """
    Obtém detalhes completos de um processo.

    Inclui configurações e últimas 5 execuções.

    Args:
        processo_id: UUID do processo
        db: Sessão do banco de dados
        service: Service de processo

    Returns:
        SuccessResponse com ProcessoDetail

    Raises:
        HTTPException 404: Se processo não encontrado
    """
    try:
        detail = service.get_processo_detail(db, processo_id)
        return success_response(data=detail)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{processo_id}",
    response_model=SuccessResponse[ProcessoResponse],
    status_code=status.HTTP_200_OK,
    summary="Atualizar processo",
    description="Atualiza os dados de um processo existente.",
    responses={
        200: {"description": "Processo atualizado"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
        409: {"description": "Conflito - nome duplicado", "model": ErrorResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def update_processo(
    processo_id: UUID,
    processo_update: ProcessoUpdate,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
) -> SuccessResponse[ProcessoResponse]:
    """
    Atualiza um processo.

    Args:
        processo_id: UUID do processo
        processo_update: Dados para atualização
        db: Sessão do banco de dados
        service: Service de processo

    Returns:
        SuccessResponse com ProcessoResponse

    Raises:
        HTTPException 404: Se processo não encontrado
        HTTPException 409: Se nome duplicado
        HTTPException 400: Se dados inválidos
    """
    try:
        processo = service.update_processo(db, processo_id, processo_update)
        return success_response(
            data=processo, message="Processo atualizado com sucesso"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{processo_id}",
    response_model=SuccessResponse[ProcessoResponse],
    status_code=status.HTTP_200_OK,
    summary="Atualizar processo parcialmente",
    description="Atualiza parcialmente os dados de um processo existente.",
    responses={
        200: {"description": "Processo atualizado"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
        409: {"description": "Conflito - nome duplicado", "model": ErrorResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def patch_processo(
    processo_id: UUID,
    processo_update: ProcessoUpdate,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
) -> SuccessResponse[ProcessoResponse]:
    """
    Atualiza parcialmente um processo.

    Mesma implementação do PUT, pois ProcessoUpdate já suporta campos opcionais.

    Args:
        processo_id: UUID do processo
        processo_update: Dados para atualização parcial
        db: Sessão do banco de dados
        service: Service de processo

    Returns:
        SuccessResponse com ProcessoResponse

    Raises:
        HTTPException 404: Se processo não encontrado
        HTTPException 409: Se nome duplicado
        HTTPException 400: Se dados inválidos
    """
    try:
        processo = service.update_processo(db, processo_id, processo_update)
        return success_response(
            data=processo, message="Processo atualizado com sucesso"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{processo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar processo",
    description="Deleta um processo e seus dados relacionados (cascata).",
    responses={
        204: {"description": "Processo deletado com sucesso"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
        409: {
            "description": "Conflito - execuções em andamento",
            "model": ErrorResponse,
        },
    },
)
def delete_processo(
    processo_id: UUID,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
):
    """
    Deleta um processo.

    Args:
        processo_id: UUID do processo
        db: Sessão do banco de dados
        service: Service de processo

    Raises:
        HTTPException 404: Se processo não encontrado
        HTTPException 409: Se há execuções em andamento
    """
    try:
        service.delete_processo(db, processo_id)
        return None  # 204 No Content
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{processo_id}/metricas",
    response_model=SuccessResponse[ProcessoMetricas],
    status_code=status.HTTP_200_OK,
    summary="Obter métricas do processo",
    description="Retorna estatísticas e métricas agregadas do processo.",
    responses={
        200: {"description": "Métricas do processo"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
    },
)
def get_processo_metricas(
    processo_id: UUID,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
) -> SuccessResponse[ProcessoMetricas]:
    """
    Obtém métricas agregadas de um processo.

    Inclui estatísticas de execuções, taxa de sucesso, páginas extraídas, etc.

    Args:
        processo_id: UUID do processo
        db: Sessão do banco de dados
        service: Service de processo

    Returns:
        SuccessResponse com ProcessoMetricas

    Raises:
        HTTPException 404: Se processo não encontrado
    """
    try:
        metricas = service.get_processo_metricas(db, processo_id)
        return success_response(data=metricas)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
