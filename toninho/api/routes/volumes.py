"""Rotas da API para gerenciamento de Volumes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from toninho.api.dependencies.volume_deps import get_volume_service
from toninho.core.database import get_db
from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import VolumeStatus
from toninho.schemas.base import BaseSchema
from toninho.schemas.responses import (
    ErrorResponse,
    SuccessListResponse,
    SuccessResponse,
    success_response,
)
from toninho.schemas.volume import (
    VolumeCreate,
    VolumeResponse,
    VolumeSummary,
    VolumeUpdate,
    VolumeValidationResult,
)
from toninho.services.volume_service import VolumeService

router = APIRouter(prefix="/api/v1/volumes", tags=["Volumes"])


class PathValidationRequest(BaseSchema):
    """Schema para requisição de validação de path."""

    path: str = Field(
        ..., min_length=1, max_length=500, description="Caminho a validar"
    )


@router.post(
    "",
    response_model=SuccessResponse[VolumeResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="Criar novo volume",
    description="Cria um novo volume de armazenamento com os dados fornecidos.",
    responses={
        201: {"description": "Volume criado com sucesso"},
        409: {
            "description": "Conflito - nome ou path duplicado",
            "model": ErrorResponse,
        },
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def create_volume(
    volume_create: VolumeCreate,
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
) -> SuccessResponse[VolumeResponse]:
    """Cria um novo volume de armazenamento."""
    try:
        volume = service.create_volume(db, volume_create)
        return success_response(data=volume)
    except ConflictError as e:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Violação de integridade de dados",
        )


@router.get(
    "",
    response_model=SuccessListResponse[VolumeResponse],
    status_code=http_status.HTTP_200_OK,
    summary="Listar volumes",
    description="Lista volumes com paginação e filtros opcionais.",
    responses={
        200: {"description": "Lista de volumes"},
        400: {"description": "Parâmetros inválidos", "model": ErrorResponse},
    },
)
def list_volumes(
    page: int = Query(1, ge=1, description="Número da página (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Registros por página"),
    status: VolumeStatus | None = Query(None, description="Filtrar por status"),
    busca: str | None = Query(None, description="Buscar por nome"),
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
) -> SuccessListResponse[VolumeResponse]:
    """Lista volumes com paginação e filtros."""
    try:
        return service.list_volumes(
            db=db,
            page=page,
            per_page=per_page,
            status=status,
            busca=busca,
        )
    except ValidationError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/ativos",
    response_model=SuccessResponse[list[VolumeSummary]],
    status_code=http_status.HTTP_200_OK,
    summary="Listar volumes ativos",
    description="Lista volumes ativos para uso em combos/selects.",
    responses={
        200: {"description": "Lista de volumes ativos"},
    },
)
def list_volumes_ativos(
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
) -> SuccessResponse[list[VolumeSummary]]:
    """Lista volumes ativos para combos/selects."""
    volumes = service.get_volumes_ativos(db)
    return success_response(data=volumes)


@router.get(
    "/{volume_id}",
    response_model=SuccessResponse[VolumeResponse],
    status_code=http_status.HTTP_200_OK,
    summary="Obter volume",
    description="Retorna os dados de um volume específico.",
    responses={
        200: {"description": "Volume encontrado"},
        404: {"description": "Volume não encontrado", "model": ErrorResponse},
    },
)
def get_volume(
    volume_id: UUID,
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
) -> SuccessResponse[VolumeResponse]:
    """Busca um volume específico pelo ID."""
    try:
        volume = service.get_volume(db, volume_id)
        return success_response(data=volume)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{volume_id}",
    response_model=SuccessResponse[VolumeResponse],
    status_code=http_status.HTTP_200_OK,
    summary="Atualizar volume",
    description="Atualiza os dados de um volume existente.",
    responses={
        200: {"description": "Volume atualizado"},
        404: {"description": "Volume não encontrado", "model": ErrorResponse},
        409: {
            "description": "Conflito - nome ou path duplicado",
            "model": ErrorResponse,
        },
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def update_volume(
    volume_id: UUID,
    volume_update: VolumeUpdate,
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
) -> SuccessResponse[VolumeResponse]:
    """Atualiza um volume existente."""
    try:
        volume = service.update_volume(db, volume_id, volume_update)
        return success_response(data=volume)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{volume_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Deletar volume",
    description="Deleta um volume de armazenamento.",
    responses={
        204: {"description": "Volume deletado com sucesso"},
        404: {"description": "Volume não encontrado", "model": ErrorResponse},
        409: {
            "description": "Conflito - configurações vinculadas",
            "model": ErrorResponse,
        },
    },
)
def delete_volume(
    volume_id: UUID,
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
) -> None:
    """Remove um volume pelo ID."""
    try:
        service.delete_volume(db, volume_id)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/{volume_id}/testar",
    response_model=SuccessResponse[VolumeValidationResult],
    status_code=http_status.HTTP_200_OK,
    summary="Testar acesso ao volume",
    description="Testa se o path do volume é acessível para leitura e escrita.",
    responses={
        200: {"description": "Resultado do teste de acesso"},
        404: {"description": "Volume não encontrado", "model": ErrorResponse},
    },
)
def test_volume(
    volume_id: UUID,
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
) -> SuccessResponse[VolumeValidationResult]:
    """Testa o acesso ao path de um volume existente."""
    try:
        result = service.test_volume(db, volume_id)
        return success_response(data=result)
    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/validar-path",
    response_model=SuccessResponse[VolumeValidationResult],
    status_code=http_status.HTTP_200_OK,
    summary="Validar path",
    description="Valida um path sem criar volume.",
    responses={
        200: {"description": "Resultado da validação do path"},
    },
)
def validate_path(
    body: PathValidationRequest,
    service: VolumeService = Depends(get_volume_service),
) -> SuccessResponse[VolumeValidationResult]:
    """Valida um path sem criar volume."""
    result = service.validate_path_access(body.path)
    return success_response(data=result)
