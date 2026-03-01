"""Rotas da API para gerenciamento de Páginas Extraídas."""

from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from toninho.api.dependencies.pagina_extraida_deps import get_pagina_extraida_service
from toninho.core.database import get_db
from toninho.core.exceptions import NotFoundError
from toninho.models.enums import PaginaStatus
from toninho.schemas.pagina_extraida import (
    EstatisticasPaginas,
    PaginaExtraidaCreate,
    PaginaExtraidaDetail,
    PaginaExtraidaResponse,
    PaginaExtraidaSummary,
)
from toninho.schemas.responses import (
    ErrorResponse,
    SuccessListResponse,
    SuccessResponse,
    success_response,
)
from toninho.services.pagina_extraida_service import PaginaExtraidaService

# ---- Router independente (/api/v1/paginas/...) ----
router = APIRouter(prefix="/api/v1", tags=["Páginas Extraídas"])

# ---- Router aninhado sob execucoes (/api/v1/execucoes/{id}/...) ----
router_execucoes = APIRouter(prefix="/api/v1/execucoes", tags=["Páginas Extraídas"])


# ---------------------------------------------------------------------------
# Criação de páginas
# ---------------------------------------------------------------------------


@router.post(
    "/paginas",
    response_model=SuccessResponse[PaginaExtraidaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar registro de página extraída",
    responses={
        201: {"description": "Página criada"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def create_pagina(
    pagina_create: PaginaExtraidaCreate,
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
) -> SuccessResponse[PaginaExtraidaResponse]:
    """Cria um novo registro de página extraída (uso interno via workers)."""
    try:
        pagina = service.create_pagina_extraida(db, pagina_create)
        return success_response(data=pagina)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValueError, Exception) as e:
        msg = str(e)
        if "erro_mensagem" in msg or "FALHOU" in msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        raise


@router.post(
    "/paginas/batch",
    response_model=SuccessResponse[List[PaginaExtraidaResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Criar múltiplas páginas em lote",
    responses={
        201: {"description": "Páginas criadas"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def create_paginas_batch(
    paginas_create: List[PaginaExtraidaCreate],
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
) -> SuccessResponse[List[PaginaExtraidaResponse]]:
    """Cria múltiplas páginas extraídas em lote."""
    try:
        paginas = service.create_pagina_extraida_batch(db, paginas_create)
        return success_response(data=paginas)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Rotas por execucao_id
# ---------------------------------------------------------------------------


@router_execucoes.get(
    "/{execucao_id}/paginas",
    response_model=SuccessListResponse[PaginaExtraidaSummary],
    status_code=status.HTTP_200_OK,
    summary="Listar páginas da execução",
    responses={
        200: {"description": "Lista de páginas"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def list_paginas_by_execucao(
    execucao_id: UUID,
    page: int = Query(default=1, ge=1, description="Número da página"),
    per_page: int = Query(default=100, ge=1, le=100, description="Itens por página"),
    status_filter: Optional[PaginaStatus] = Query(
        default=None, alias="status", description="Filtrar por status"
    ),
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
) -> SuccessListResponse[PaginaExtraidaSummary]:
    """Lista páginas extraídas de uma execução com paginação."""
    try:
        return service.list_paginas_by_execucao(
            db, execucao_id, page=page, per_page=per_page, status=status_filter
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router_execucoes.get(
    "/{execucao_id}/paginas/estatisticas",
    response_model=SuccessResponse[EstatisticasPaginas],
    status_code=status.HTTP_200_OK,
    summary="Obter estatísticas de extração",
    responses={
        200: {"description": "Estatísticas calculadas"},
        404: {"description": "Execução não encontrada", "model": ErrorResponse},
    },
)
def get_estatisticas_paginas(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
) -> SuccessResponse[EstatisticasPaginas]:
    """Retorna estatísticas de extração de páginas de uma execução."""
    try:
        estatisticas = service.get_estatisticas_paginas(db, execucao_id)
        return success_response(data=estatisticas)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Rotas por pagina_id
# ---------------------------------------------------------------------------


@router.get(
    "/paginas/{pagina_id}",
    response_model=SuccessResponse[PaginaExtraidaDetail],
    status_code=status.HTTP_200_OK,
    summary="Obter metadados de página extraída",
    responses={
        200: {"description": "Página encontrada"},
        404: {"description": "Página não encontrada", "model": ErrorResponse},
    },
)
def get_pagina(
    pagina_id: UUID,
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
) -> SuccessResponse[PaginaExtraidaDetail]:
    """Busca metadados de uma página extraída específica."""
    try:
        pagina = service.get_pagina_extraida(db, pagina_id)
        return success_response(data=pagina)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/paginas/{pagina_id}/download",
    summary="Download do arquivo markdown",
    responses={
        200: {"description": "Arquivo para download"},
        404: {"description": "Página ou arquivo não encontrado", "model": ErrorResponse},
    },
)
def download_pagina(
    pagina_id: UUID,
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
):
    """Faz download do arquivo markdown de uma página extraída."""
    try:
        pagina = service.get_pagina_extraida(db, pagina_id)

        filepath = Path(pagina.caminho_arquivo)
        if not filepath.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo não encontrado no filesystem",
            )

        filename = filepath.name

        return FileResponse(
            path=str(filepath),
            media_type="text/markdown",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado no filesystem",
        )


@router.delete(
    "/paginas/{pagina_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar página extraída",
    responses={
        204: {"description": "Página deletada (sem conteúdo)"},
        404: {"description": "Página não encontrada", "model": ErrorResponse},
    },
)
def delete_pagina(
    pagina_id: UUID,
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
):
    """Deleta uma página extraída (metadados + arquivo do filesystem)."""
    try:
        service.delete_pagina(db, pagina_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
