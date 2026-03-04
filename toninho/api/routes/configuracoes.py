"""Rotas da API para gerenciamento de Configurações."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from toninho.api.dependencies.configuracao_deps import get_configuracao_service
from toninho.core.database import get_db
from toninho.core.exceptions import NotFoundError, ValidationError
from toninho.schemas.configuracao import (
    AgendamentoInfo,
    ConfiguracaoCreate,
    ConfiguracaoResponse,
    ConfiguracaoUpdate,
)
from toninho.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    success_response,
)
from toninho.services.configuracao_service import ConfiguracaoService

# ---- Router aninhado sob processos (/api/v1/processos/{processo_id}/...) ----
router_processos = APIRouter(prefix="/api/v1/processos", tags=["Configurações"])

# ---- Router independente (/api/v1/configuracoes/...) ----
router = APIRouter(prefix="/api/v1/configuracoes", tags=["Configurações"])


# ---------------------------------------------------------------------------
# Sub-rotas de processo
# ---------------------------------------------------------------------------


@router_processos.post(
    "/{processo_id}/configuracoes",
    response_model=SuccessResponse[ConfiguracaoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar configuração para o processo",
    responses={
        201: {"description": "Configuração criada"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def create_configuracao(
    processo_id: UUID,
    config_create: ConfiguracaoCreate,
    db: Session = Depends(get_db),
    service: ConfiguracaoService = Depends(get_configuracao_service),
) -> SuccessResponse[ConfiguracaoResponse]:
    """Cria uma nova configuração para o processo."""
    try:
        configuracao = service.create_configuracao(db, processo_id, config_create)
        return success_response(data=configuracao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router_processos.get(
    "/{processo_id}/configuracoes",
    response_model=SuccessResponse[list[ConfiguracaoResponse]],
    status_code=status.HTTP_200_OK,
    summary="Listar histórico de configurações do processo",
    responses={
        200: {"description": "Lista de configurações"},
        404: {"description": "Processo não encontrado", "model": ErrorResponse},
    },
)
def list_configuracoes(
    processo_id: UUID,
    db: Session = Depends(get_db),
    service: ConfiguracaoService = Depends(get_configuracao_service),
) -> SuccessResponse[list[ConfiguracaoResponse]]:
    """Lista todas as configurações (histórico) de um processo."""
    try:
        configuracoes = service.list_configuracoes_by_processo(db, processo_id)
        return success_response(data=configuracoes)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router_processos.get(
    "/{processo_id}/configuracao",
    response_model=SuccessResponse[ConfiguracaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Obter configuração atual do processo",
    responses={
        200: {"description": "Configuração atual"},
        404: {
            "description": "Processo/configuração não encontrado",
            "model": ErrorResponse,
        },
    },
)
def get_configuracao_by_processo(
    processo_id: UUID,
    db: Session = Depends(get_db),
    service: ConfiguracaoService = Depends(get_configuracao_service),
) -> SuccessResponse[ConfiguracaoResponse]:
    """Retorna a configuração mais recente de um processo."""
    try:
        configuracao = service.get_configuracao_by_processo(db, processo_id)
        return success_response(data=configuracao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Rotas por ID de configuração
# ---------------------------------------------------------------------------


@router.get(
    "/{config_id}",
    response_model=SuccessResponse[ConfiguracaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Obter configuração por ID",
    responses={
        200: {"description": "Configuração encontrada"},
        404: {"description": "Configuração não encontrada", "model": ErrorResponse},
    },
)
def get_configuracao(
    config_id: UUID,
    db: Session = Depends(get_db),
    service: ConfiguracaoService = Depends(get_configuracao_service),
) -> SuccessResponse[ConfiguracaoResponse]:
    """Busca uma configuração específica pelo ID."""
    try:
        configuracao = service.get_configuracao(db, config_id)
        return success_response(data=configuracao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{config_id}",
    response_model=SuccessResponse[ConfiguracaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Atualizar configuração",
    responses={
        200: {"description": "Configuração atualizada"},
        404: {"description": "Configuração não encontrada", "model": ErrorResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
    },
)
def update_configuracao(
    config_id: UUID,
    config_update: ConfiguracaoUpdate,
    db: Session = Depends(get_db),
    service: ConfiguracaoService = Depends(get_configuracao_service),
) -> SuccessResponse[ConfiguracaoResponse]:
    """Atualiza uma configuração existente."""
    try:
        configuracao = service.update_configuracao(db, config_id, config_update)
        return success_response(data=configuracao)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar configuração",
    responses={
        204: {"description": "Configuração deletada"},
        404: {"description": "Configuração não encontrada", "model": ErrorResponse},
    },
)
def delete_configuracao(
    config_id: UUID,
    db: Session = Depends(get_db),
    service: ConfiguracaoService = Depends(get_configuracao_service),
) -> None:
    """Remove uma configuração pelo ID."""
    try:
        service.delete_configuracao(db, config_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{config_id}/validar-agendamento",
    response_model=SuccessResponse[AgendamentoInfo],
    status_code=status.HTTP_200_OK,
    summary="Validar expressão cron da configuração",
    responses={
        200: {"description": "Resultado da validação"},
        404: {"description": "Configuração não encontrada", "model": ErrorResponse},
    },
)
def validar_agendamento(
    config_id: UUID,
    db: Session = Depends(get_db),
    service: ConfiguracaoService = Depends(get_configuracao_service),
) -> SuccessResponse[AgendamentoInfo]:
    """Valida a expressão cron da configuração e retorna próximas execuções."""
    try:
        configuracao = service.get_configuracao(db, config_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    cron = configuracao.agendamento_cron or ""
    info = service.validar_agendamento(cron)
    return success_response(data=info)
