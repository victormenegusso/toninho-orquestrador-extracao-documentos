"""Rotas da API para gerenciamento de Execuções."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from toninho.api.dependencies.execucao_deps import get_execucao_service
from toninho.core.database import get_db
from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import ExecucaoStatus
from toninho.schemas.execucao import (
    ExecucaoDetail,
    ExecucaoMetricas,
    ExecucaoResponse,
    ExecucaoStatusUpdate,
    ExecucaoSummary,
    ProgressoResponse,
)
from toninho.schemas.responses import (
    ErrorResponse,
    SuccessListResponse,
    SuccessResponse,
    success_response,
)
from toninho.services.execucao_service import ExecucaoService

# ---- Router aninhado sob processos ----
router_processos = APIRouter(prefix="/api/v1/processos", tags=["Execuções"])

# ---- Router independente ----
router = APIRouter(prefix="/api/v1/execucoes", tags=["Execuções"])


# ---------------------------------------------------------------------------
# Sub-rotas de processo
# ---------------------------------------------------------------------------


@router_processos.post(
    "/{processo_id}/execucoes",
    response_model=SuccessResponse[ExecucaoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar e iniciar execução do processo",
    responses={
        201: {"description": "Execução criada e enfileirada"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
        409: {"description": "Já há execução em andamento", "model": ErrorResponse},
    },
)
def create_execucao(
    processo_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoResponse]:
    """Cria e enfileira uma nova execução para o processo."""
    try:
        execucao = service.create_execucao(db, processo_id)
        return success_response(data=execucao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router_processos.get(
    "/{processo_id}/execucoes",
    response_model=SuccessListResponse[ExecucaoSummary],
    status_code=status.HTTP_200_OK,
    summary="Listar execuções do processo",
    responses={
        200: {"description": "Lista de execuções"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
    },
)
def list_execucoes_by_processo(
    processo_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: ExecucaoStatus | None = Query(None),
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessListResponse[ExecucaoSummary]:
    """Lista execuções de um processo com paginação."""
    try:
        return service.list_execucoes(
            db=db,
            page=page,
            per_page=per_page,
            processo_id=processo_id,
            status=status,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Rotas globais de execução
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SuccessListResponse[ExecucaoSummary],
    status_code=status.HTTP_200_OK,
    summary="Listar todas as execuções",
)
def list_execucoes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: ExecucaoStatus | None = Query(None),
    processo_id: UUID | None = Query(None),
    ordem: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessListResponse[ExecucaoSummary]:
    """Lista todas as execuções com paginação."""
    return service.list_execucoes(
        db=db,
        page=page,
        per_page=per_page,
        status=status,
        processo_id=processo_id,
        ordem=ordem,
    )


@router.get(
    "/{execucao_id}",
    response_model=SuccessResponse[ExecucaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes básicos da execução",
    responses={
        200: {"description": "Execução encontrada"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def get_execucao(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoResponse]:
    """Retorna detalhes básicos de uma execução."""
    try:
        execucao = service.get_execucao(db, execucao_id)
        return success_response(data=execucao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{execucao_id}/detalhes",
    response_model=SuccessResponse[ExecucaoDetail],
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes completos da execução",
    responses={
        200: {"description": "Detalhes completos"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def get_execucao_detalhes(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoDetail]:
    """Retorna detalhes completos de uma execução (métricas incluídas)."""
    try:
        detalhe = service.get_execucao_detail(db, execucao_id)
        return success_response(data=detalhe)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{execucao_id}/status",
    response_model=SuccessResponse[ExecucaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Atualizar status manualmente",
    responses={
        200: {"description": "Status atualizado"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
        400: {"description": "Transição de status inválida", "model": ErrorResponse},
    },
)
def update_execucao_status(
    execucao_id: UUID,
    status_update: ExecucaoStatusUpdate,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoResponse]:
    """Atualiza manualmente o status de uma execução."""
    try:
        execucao = service.update_execucao_status(db, execucao_id, status_update)
        return success_response(data=execucao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{execucao_id}/cancelar",
    response_model=SuccessResponse[ExecucaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Cancelar execução",
    responses={
        200: {"description": "Execução cancelada"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
        409: {"description": "Execução não pode ser cancelada", "model": ErrorResponse},
    },
)
def cancelar_execucao(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoResponse]:
    """Cancela uma execução em andamento."""
    try:
        execucao = service.cancelar_execucao(db, execucao_id)
        return success_response(data=execucao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/{execucao_id}/pausar",
    response_model=SuccessResponse[ExecucaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Pausar execução",
    responses={
        200: {"description": "Execução pausada"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
        409: {"description": "Execução não pode ser pausada", "model": ErrorResponse},
    },
)
def pausar_execucao(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoResponse]:
    """Pausa uma execução em andamento."""
    try:
        execucao = service.pausar_execucao(db, execucao_id)
        return success_response(data=execucao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/{execucao_id}/retomar",
    response_model=SuccessResponse[ExecucaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Retomar execução pausada",
    responses={
        200: {"description": "Execução retomada"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
        409: {"description": "Execução não pode ser retomada", "model": ErrorResponse},
    },
)
def retomar_execucao(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoResponse]:
    """Retoma uma execução pausada."""
    try:
        execucao = service.retomar_execucao(db, execucao_id)
        return success_response(data=execucao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{execucao_id}/progresso",
    response_model=SuccessResponse[ProgressoResponse],
    status_code=status.HTTP_200_OK,
    summary="Obter progresso em tempo real",
    responses={
        200: {"description": "Progresso da execução"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def get_progresso(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ProgressoResponse]:
    """Retorna progresso em tempo real da execução (para polling)."""
    try:
        progresso = service.get_progresso(db, execucao_id)
        return success_response(data=progresso)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{execucao_id}/metricas",
    response_model=SuccessResponse[ExecucaoMetricas],
    status_code=status.HTTP_200_OK,
    summary="Obter métricas detalhadas",
    responses={
        200: {"description": "Métricas da execução"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def get_metricas(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> SuccessResponse[ExecucaoMetricas]:
    """Retorna métricas detalhadas de uma execução."""
    try:
        metricas = service.get_execucao_metricas(db, execucao_id)
        return success_response(data=metricas)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{execucao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar execução",
    responses={
        204: {"description": "Execução deletada"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
        409: {"description": "Execução em andamento", "model": ErrorResponse},
    },
)
def delete_execucao(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
) -> None:
    """Remove uma execução (não permitido se EM_EXECUCAO)."""
    try:
        service.delete_execucao(db, execucao_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
