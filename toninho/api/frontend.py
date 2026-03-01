"""
Router Frontend para o Toninho.

Serve as páginas HTML do sistema usando Jinja2 templates.
Rotas de páginas gerais: home, dashboard.
Rotas de processos: list, create, edit, detail, search (HTMX partial).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from toninho.api.dependencies.processo_deps import get_processo_service
from toninho.core.database import get_db
from toninho.core.exceptions import NotFoundError
from toninho.models.enums import ProcessoStatus
from toninho.services.processo_service import ProcessoService

router = APIRouter(tags=["Frontend"])

# Configurar templates
templates = Jinja2Templates(directory="frontend/templates")


def get_template_context(request: Request, **kwargs) -> dict:
    """
    Adiciona contexto global a todos os templates.

    Args:
        request: Request object do FastAPI
        **kwargs: Contexto adicional específico da página

    Returns:
        dict com contexto completo para o template
    """
    return {
        "request": request,
        "app_name": "Toninho",
        "version": "1.0.0",
        **kwargs,
    }


# ==================== Rotas Gerais ====================


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    """Página inicial - redireciona para dashboard."""
    context = get_template_context(request, title="Home")
    return templates.TemplateResponse("pages/home.html", context)


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    """Dashboard principal com estatísticas gerais."""
    # Stats padrão - em uma implementação completa viriam do banco de dados
    default_stats = {
        "total_processos": 0,
        "processos_ativos": 0,
        "execucoes_hoje": 0,
        "taxa_sucesso": 0,
    }
    context = get_template_context(request, title="Dashboard", stats=default_stats)
    return templates.TemplateResponse("pages/dashboard/index.html", context)


# ==================== Rotas de Processos ====================


@router.get(
    "/processos/novo",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def processos_create(request: Request):
    """Formulário de criação de novo processo."""
    context = get_template_context(
        request,
        title="Novo Processo",
        processo=None,
        errors={},
    )
    return templates.TemplateResponse("pages/processos/create.html", context)


@router.get(
    "/processos/search",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def processos_search(
    request: Request,
    search: Optional[str] = Query(None, alias="search"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
):
    """
    Busca processos (partial HTMX).

    Retorna apenas a tabela parcial para ser inserida via HTMX swap.
    """
    status_filter = _parse_status_filter(status)
    processos = service.list_processos(
        db, page=1, per_page=20, status=status_filter, busca=search
    )
    context = get_template_context(request, processos=processos)
    return templates.TemplateResponse("partials/processos_table.html", context)


@router.get(
    "/processos",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def processos_list(
    request: Request,
    page: int = Query(1, ge=1),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
):
    """Lista de processos com paginação e filtros."""
    status_filter = _parse_status_filter(status)
    processos = service.list_processos(
        db,
        page=page,
        per_page=20,
        status=status_filter,
        busca=search,
    )
    context = get_template_context(
        request,
        title="Processos",
        processos=processos,
        status_filter=status or "",
        search=search or "",
    )
    return templates.TemplateResponse("pages/processos/list.html", context)


@router.get(
    "/processos/{id}/editar",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def processos_edit(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
):
    """Formulário de edição de processo existente."""
    try:
        processo = service.get_processo_detail(db, id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    context = get_template_context(
        request,
        title=f"Editar: {processo.nome}",
        processo=processo,
        errors={},
    )
    return templates.TemplateResponse("pages/processos/create.html", context)


@router.get(
    "/processos/{id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def processos_detail(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    service: ProcessoService = Depends(get_processo_service),
):
    """Página de detalhes de um processo."""
    try:
        processo = service.get_processo_detail(db, id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    context = get_template_context(
        request,
        title=processo.nome,
        processo=processo,
    )
    return templates.TemplateResponse("pages/processos/detail.html", context)


# ==================== Helpers ====================


def _parse_status_filter(status: Optional[str]) -> Optional[ProcessoStatus]:
    """
    Converte string de status para enum ProcessoStatus.

    Args:
        status: String do status (ex: "ATIVO", "INATIVO")

    Returns:
        ProcessoStatus enum ou None se inválido/vazio
    """
    if not status:
        return None
    try:
        return ProcessoStatus(status.upper())
    except ValueError:
        return None

