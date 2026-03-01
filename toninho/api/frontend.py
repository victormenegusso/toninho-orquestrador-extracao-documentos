"""
Router Frontend para o Toninho.

Serve as páginas HTML do sistema usando Jinja2 templates.
Rotas de páginas gerais: home, dashboard.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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
