"""
Router Frontend para o Toninho.

Serve as páginas HTML do sistema usando Jinja2 templates.
Rotas de páginas gerais: home, dashboard.
Rotas de processos: list, create, edit, detail, search (HTMX partial).
Rotas de execuções: list, detail, progress partial, ativas partial.
Rotas de páginas extraídas: list por execução, detail, search partial.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from toninho.api.dependencies.configuracao_deps import get_configuracao_service
from toninho.api.dependencies.execucao_deps import get_execucao_service
from toninho.api.dependencies.pagina_extraida_deps import get_pagina_extraida_service
from toninho.api.dependencies.processo_deps import get_processo_service
from toninho.api.dependencies.volume_deps import get_volume_service
from toninho.core.database import get_db
from toninho.core.exceptions import NotFoundError
from toninho.models.enums import (
    ExecucaoStatus,
    FormatoSaida,
    PaginaStatus,
    ProcessoStatus,
)
from toninho.services.configuracao_service import ConfiguracaoService
from toninho.services.execucao_service import ExecucaoService
from toninho.services.pagina_extraida_service import PaginaExtraidaService
from toninho.services.processo_service import ProcessoService
from toninho.services.volume_service import VolumeService

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
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard principal com estatísticas gerais."""
    from toninho.models.enums import ExecucaoStatus as ExStatus
    from toninho.monitoring.metrics import MetricsService
    from toninho.repositories.execucao_repository import ExecucaoRepository
    from toninho.repositories.processo_repository import ProcessoRepository
    from toninho.services.execucao_service import ExecucaoService

    # Stats padrão - fallback caso db não esteja disponível
    default_stats = {
        "total_processos": 0,
        "processos_ativos": 0,
        "execucoes_hoje": 0,
        "taxa_sucesso": 0,
    }
    metrics = {
        "executions": {"total": 0, "active": 0, "completed": 0, "failed": 0},
        "success_rate": 0.0,
    }
    execucoes_ativas = []

    try:
        metrics_svc = MetricsService(db=db)
        metrics = metrics_svc.get_dashboard_metrics()
        default_stats["total_processos"] = metrics.get("processes", {}).get("total", 0)
        default_stats["execucoes_hoje"] = metrics.get("executions", {}).get("total", 0)
        default_stats["taxa_sucesso"] = metrics.get("success_rate", 0)
    except Exception:
        pass

    try:
        execucao_svc = ExecucaoService(
            repository=ExecucaoRepository(),
            processo_repository=ProcessoRepository(),
        )
        resp = execucao_svc.list_execucoes(
            db, page=1, per_page=5, status=ExStatus.EM_EXECUCAO
        )
        execucoes_ativas = resp.data
    except Exception:
        execucoes_ativas = []

    context = get_template_context(
        request,
        title="Dashboard",
        stats=default_stats,
        metrics=metrics,
        execucoes=execucoes_ativas,
    )
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
    search: str | None = Query(None, alias="search"),
    status: str | None = Query(None),
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
    status: str | None = Query(None),
    search: str | None = Query(None),
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


# ==================== Rotas de Execuções ====================


@router.get(
    "/dashboard/stats",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def dashboard_stats(request: Request, db: Session = Depends(get_db)):
    """Stats cards partial para polling do dashboard."""
    from toninho.monitoring.metrics import MetricsService

    try:
        metrics_svc = MetricsService(db=db)
        metrics = metrics_svc.get_dashboard_metrics()
    except Exception:
        metrics = {
            "executions": {"total": 0, "active": 0, "completed": 0, "failed": 0},
            "success_rate": 0.0,
        }
    context = get_template_context(request, metrics=metrics)
    return templates.TemplateResponse("partials/dashboard_stats.html", context)


@router.get(
    "/execucoes/ativas",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def execucoes_ativas_partial(
    request: Request,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
):
    """Execuções ativas partial para polling do dashboard."""
    execucoes_resp = service.list_execucoes(
        db,
        page=1,
        per_page=10,
        status=ExecucaoStatus.EM_EXECUCAO,
    )
    context = get_template_context(request, execucoes=execucoes_resp.data)
    return templates.TemplateResponse("partials/execucoes_ativas.html", context)


@router.get(
    "/execucoes/{id}/progress",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def execucao_progress(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
):
    """Progress bar partial para polling de detalhe de execução."""
    try:
        execucao = service.get_execucao(db, id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    context = get_template_context(request, execucao=execucao)
    return templates.TemplateResponse("partials/progress_bar.html", context)


@router.get(
    "/execucoes",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def execucoes_list(
    request: Request,
    page: int = Query(1, ge=1),
    status: str | None = Query(None),
    processo_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
):
    """Lista de todas as execuções com paginação."""
    status_filter = _parse_execucao_status_filter(status)
    execucoes_resp = service.list_execucoes(
        db, page=page, per_page=20, status=status_filter, processo_id=processo_id
    )
    context = get_template_context(
        request,
        title="Execuções",
        execucoes=execucoes_resp.data,
        meta=execucoes_resp.meta,
        status_filter=status or "",
        processo_id=str(processo_id) if processo_id else "",
    )
    return templates.TemplateResponse("pages/execucoes/list.html", context)


@router.get(
    "/execucoes/{id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def execucoes_detail(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    service: ExecucaoService = Depends(get_execucao_service),
):
    """Página de detalhes de uma execução com streaming de logs."""
    try:
        execucao = service.get_execucao_detail(db, id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Execução não encontrada")

    context = get_template_context(
        request,
        title=f"Execução {str(id)[:8]}",
        execucao=execucao,
    )
    return templates.TemplateResponse("pages/execucoes/detail.html", context)


# ==================== Rotas de Páginas Extraídas ====================


@router.get(
    "/paginas/search",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def paginas_search(
    request: Request,
    execucao_id: UUID = Query(...),
    search: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
):
    """Busca páginas extraídas (partial HTMX)."""
    status_filter = _parse_pagina_status_filter(status)
    paginas_resp = service.list_paginas_by_execucao(
        db,
        execucao_id,
        page=1,
        per_page=12,
        status=status_filter,
    )
    context = get_template_context(request, paginas=paginas_resp)
    return templates.TemplateResponse("partials/paginas_grid.html", context)


@router.get(
    "/execucoes/{execucao_id}/paginas",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def execucao_paginas(
    request: Request,
    execucao_id: UUID,
    page: int = Query(1, ge=1),
    status: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    execucao_service: ExecucaoService = Depends(get_execucao_service),
    pagina_service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
    config_service: ConfiguracaoService = Depends(get_configuracao_service),
):
    """Lista páginas extraídas de uma execução."""
    try:
        execucao = execucao_service.get_execucao(db, execucao_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Execução não encontrada")

    # Determinar formato_saida do processo
    formato_saida = FormatoSaida.MULTIPLOS_ARQUIVOS.value
    try:
        config = config_service.get_configuracao_by_processo(db, execucao.processo_id)
        formato_saida = config.formato_saida
    except Exception:
        pass

    status_filter = _parse_pagina_status_filter(status)
    paginas_resp = pagina_service.list_paginas_by_execucao(
        db,
        execucao_id,
        page=page,
        per_page=12,
        status=status_filter,
    )

    try:
        estatisticas = pagina_service.get_estatisticas_paginas(db, execucao_id)
        total_size_bytes = estatisticas.tamanho_total_bytes
    except Exception:
        estatisticas = None
        total_size_bytes = 0

    total_size_formatted = _format_bytes(total_size_bytes)

    context = get_template_context(
        request,
        title="Páginas Extraídas",
        execucao=execucao,
        paginas=paginas_resp,
        estatisticas=estatisticas,
        total_size_formatted=total_size_formatted,
        formato_saida=formato_saida,
        status_filter=status or "",
        search=search or "",
    )
    return templates.TemplateResponse("pages/execucoes/paginas.html", context)


@router.get(
    "/paginas/{id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def pagina_detail(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    service: PaginaExtraidaService = Depends(get_pagina_extraida_service),
):
    """Página de detalhes de uma página extraída."""
    try:
        pagina = service.get_pagina_extraida(db, id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Página não encontrada")

    context = get_template_context(
        request,
        title=pagina.url_original,
        pagina=pagina,
    )
    return templates.TemplateResponse("pages/paginas/detail.html", context)


# ==================== Rotas de Volumes ====================


@router.get(
    "/volumes",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def volumes_list(
    request: Request,
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
):
    """Lista de volumes de armazenamento."""
    volumes_resp = service.list_volumes(db, page=1, per_page=100)
    context = get_template_context(
        request,
        title="Volumes",
        volumes=volumes_resp.data,
    )
    return templates.TemplateResponse("pages/volumes/list.html", context)


@router.get(
    "/volumes/novo",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def volumes_create(request: Request):
    """Formulário de criação de novo volume."""
    context = get_template_context(
        request,
        title="Novo Volume",
        volume=None,
    )
    return templates.TemplateResponse("pages/volumes/form.html", context)


@router.get(
    "/volumes/{id}/editar",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def volumes_edit(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    service: VolumeService = Depends(get_volume_service),
):
    """Formulário de edição de volume existente."""
    try:
        volume = service.get_volume(db, id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Volume não encontrado")
    volume_dict = volume.model_dump(mode="json")
    context = get_template_context(
        request,
        title=f"Editar: {volume.nome}",
        volume=volume_dict,
    )
    return templates.TemplateResponse("pages/volumes/form.html", context)


# ==================== Helpers ====================


def _parse_status_filter(status: str | None) -> ProcessoStatus | None:
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


def _parse_execucao_status_filter(status: str | None) -> ExecucaoStatus | None:
    """Converte string de status para enum ExecucaoStatus."""
    if not status:
        return None
    try:
        return ExecucaoStatus(status.lower())
    except ValueError:
        return None


def _parse_pagina_status_filter(status: str | None) -> PaginaStatus | None:
    """Converte string de status para enum PaginaStatus."""
    if not status:
        return None
    try:
        return PaginaStatus(status.lower())
    except ValueError:
        return None


def _format_bytes(size_bytes: int) -> str:
    """Formata bytes para exibição legível (KB, MB, GB)."""
    if size_bytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"
