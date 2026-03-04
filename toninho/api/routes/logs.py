"""Rotas da API para gerenciamento de Logs."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from toninho.api.dependencies.log_deps import get_log_service
from toninho.core.database import get_db
from toninho.core.exceptions import NotFoundError
from toninho.models.enums import LogNivel
from toninho.schemas.log import LogCreate, LogEstatisticas, LogFilter, LogResponse
from toninho.schemas.responses import (
    ErrorResponse,
    SuccessListResponse,
    SuccessResponse,
    success_response,
)
from toninho.services.log_service import LogService

# ---- Router independente (/api/v1/logs/...) ----
router = APIRouter(prefix="/api/v1", tags=["Logs"])

# ---- Router aninhado sob execucoes (/api/v1/execucoes/{id}/...) ----
router_execucoes = APIRouter(prefix="/api/v1/execucoes", tags=["Logs"])


# ---------------------------------------------------------------------------
# Criação de logs
# ---------------------------------------------------------------------------


@router.post(
    "/logs",
    response_model=SuccessResponse[LogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar log",
    responses={
        201: {"description": "Log criado"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def create_log(
    log_create: LogCreate,
    db: Session = Depends(get_db),
    service: LogService = Depends(get_log_service),
) -> SuccessResponse[LogResponse]:
    """Cria um novo registro de log (uso interno via workers)."""
    try:
        log = service.create_log(db, log_create)
        return success_response(data=log)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/logs/batch",
    response_model=SuccessResponse[list[LogResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Criar múltiplos logs em lote",
    responses={
        201: {"description": "Logs criados"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def create_log_batch(
    logs_create: list[LogCreate],
    db: Session = Depends(get_db),
    service: LogService = Depends(get_log_service),
) -> SuccessResponse[list[LogResponse]]:
    """Cria múltiplos logs em lote."""
    try:
        logs = service.create_log_batch(db, logs_create)
        return success_response(data=logs)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Rotas por execucao_id
# ---------------------------------------------------------------------------


@router_execucoes.get(
    "/{execucao_id}/logs",
    response_model=SuccessListResponse[LogResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar logs da execução",
    responses={
        200: {"description": "Lista de logs"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def list_logs_by_execucao(
    execucao_id: UUID,
    page: int = Query(default=1, ge=1, description="Número da página"),
    per_page: int = Query(default=100, ge=1, le=100, description="Itens por página"),
    nivel: LogNivel | None = Query(default=None, description="Filtrar por nível"),
    desde: str | None = Query(default=None, description="Filtrar desde (ISO 8601)"),
    ate: str | None = Query(default=None, description="Filtrar até (ISO 8601)"),
    busca: str | None = Query(default=None, description="Busca na mensagem"),
    db: Session = Depends(get_db),
    service: LogService = Depends(get_log_service),
) -> SuccessListResponse[LogResponse]:
    """Lista logs de uma execução com paginação e filtros."""
    try:
        from datetime import datetime

        filtro = LogFilter(
            nivel=nivel,
            desde=datetime.fromisoformat(desde) if desde else None,
            ate=datetime.fromisoformat(ate) if ate else None,
            busca=busca,
        )
        return service.list_logs_by_execucao(
            db, execucao_id, page=page, per_page=per_page, filtro=filtro
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router_execucoes.get(
    "/{execucao_id}/logs/recentes",
    response_model=SuccessResponse[list[LogResponse]],
    status_code=status.HTTP_200_OK,
    summary="Obter últimos logs da execução",
    responses={
        200: {"description": "Logs recentes"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def get_logs_recentes(
    execucao_id: UUID,
    limit: int = Query(default=20, ge=1, le=100, description="Número de logs"),
    db: Session = Depends(get_db),
    service: LogService = Depends(get_log_service),
) -> SuccessResponse[list[LogResponse]]:
    """Retorna os últimos N logs de uma execução."""
    try:
        logs = service.get_logs_recentes(db, execucao_id, limit=limit)
        return success_response(data=logs)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router_execucoes.get(
    "/{execucao_id}/logs/estatisticas",
    response_model=SuccessResponse[LogEstatisticas],
    status_code=status.HTTP_200_OK,
    summary="Obter estatísticas de logs da execução",
    responses={
        200: {"description": "Estatísticas calculadas"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def get_estatisticas_logs(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: LogService = Depends(get_log_service),
) -> SuccessResponse[LogEstatisticas]:
    """Retorna estatísticas de logs de uma execução."""
    try:
        estatisticas = service.get_estatisticas_logs(db, execucao_id)
        return success_response(data=estatisticas)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router_execucoes.get(
    "/{execucao_id}/logs/stream",
    summary="Stream de logs em tempo real (SSE)",
    responses={
        200: {"description": "Stream de eventos"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
async def stream_logs(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: LogService = Depends(get_log_service),
):
    """Stream de logs em tempo real via Server-Sent Events."""
    from asyncio import sleep

    from sqlalchemy import select as sa_select

    from toninho.models.enums import ExecucaoStatus
    from toninho.models.log import Log

    # Verificar execução existe
    from toninho.repositories.execucao_repository import ExecucaoRepository

    execucao_repo = ExecucaoRepository()
    execucao = execucao_repo.get_by_id(db, execucao_id)
    if not execucao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execucao com identificador '{execucao_id}' não encontrado",
        )

    ESTADOS_FINAIS = {
        ExecucaoStatus.CONCLUIDO,
        ExecucaoStatus.FALHOU,
        ExecucaoStatus.CANCELADO,
        ExecucaoStatus.CONCLUIDO_COM_ERROS,
    }

    async def event_generator():
        ultimo_id = None
        while True:
            # Buscar novos logs desde o último ID
            stmt = (
                sa_select(Log)
                .where(Log.execucao_id == execucao_id)
                .order_by(Log.timestamp.asc())
            )
            if ultimo_id is not None:
                from sqlalchemy import select as sel

                from toninho.models.log import Log as LogModel

                # Filter logs com id > ultimo_id by timestamp comparison
                ultimo_log = db.execute(
                    sel(LogModel).where(LogModel.id == ultimo_id)
                ).scalar_one_or_none()
                if ultimo_log:
                    stmt = stmt.where(Log.timestamp > ultimo_log.timestamp)

            novos_logs = list(db.execute(stmt).scalars().all())
            for log in novos_logs:
                log_response = LogResponse.model_validate(log)
                yield f"data: {log_response.model_dump_json()}\n\n"
                ultimo_id = log.id

            # Verificar se execução finalizou (re-query para estado atualizado)
            execucao_atual = execucao_repo.get_by_id(db, execucao_id)
            if execucao_atual is None or execucao_atual.status in ESTADOS_FINAIS:
                yield "event: done\ndata: {}\n\n"
                break

            await sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Rotas por log_id
# ---------------------------------------------------------------------------


@router.get(
    "/logs/{log_id}",
    response_model=SuccessResponse[LogResponse],
    status_code=status.HTTP_200_OK,
    summary="Obter log por ID",
    responses={
        200: {"description": "Log encontrado"},
        404: {"description": "Log não encontrado", "model": ErrorResponse},
    },
)
def get_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    service: LogService = Depends(get_log_service),
) -> SuccessResponse[LogResponse]:
    """Busca um log específico pelo ID."""
    try:
        log = service.get_log(db, log_id)
        return success_response(data=log)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
