"""
Arquivo principal da aplicação Toninho.

Este módulo inicializa a aplicação FastAPI e configura todas as rotas,
middlewares e dependências necessárias.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# from toninho.api.routes import health
from toninho.api.routes import processos
from toninho.api.routes import configuracoes
from toninho.api.routes import execucoes
from toninho.api.routes import logs
from toninho.api.routes import paginas_extraidas
from toninho.core.config import settings
from toninho.core.logging import setup_logging

# Configurar logging
logger = setup_logging()

# Criar aplicação FastAPI
app = FastAPI(
    title="Toninho - Extrator de Processos",
    description="Sistema de extração de dados de processos judiciais",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Montar arquivos estáticos
# app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Configurar templates
# templates = Jinja2Templates(directory="frontend/templates")

# Registrar rotas
# app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(processos.router)
app.include_router(configuracoes.router_processos)
app.include_router(configuracoes.router)
app.include_router(execucoes.router_processos)
app.include_router(execucoes.router)
app.include_router(logs.router_execucoes)
app.include_router(logs.router)
app.include_router(paginas_extraidas.router_execucoes)
app.include_router(paginas_extraidas.router)


@app.get("/")
async def root():
    """Endpoint raiz - retorna informações básicas da API."""
    return {
        "name": "Toninho",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint para Docker e monitoramento."""
    return {"status": "healthy", "service": "toninho"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "toninho.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
