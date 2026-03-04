"""
Arquivo principal da aplicação Toninho.

Este módulo inicializa a aplicação FastAPI e configura todas as rotas,
middlewares e dependências necessárias.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from toninho.api import frontend
from toninho.api.routes import (
    configuracoes,
    execucoes,
    health,
    logs,
    monitoring,
    paginas_extraidas,
    processos,
)
from toninho.core.config import settings
from toninho.core.logging import setup_logging

# Configurar logging
logger = setup_logging()

# Criar aplicação FastAPI
app = FastAPI(
    title="Toninho - Extrator de Processos",
    description="Sistema de extração de dados de processos",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Registrar rotas da API
app.include_router(health.router)
app.include_router(processos.router)
app.include_router(configuracoes.router_processos)
app.include_router(configuracoes.router)
app.include_router(execucoes.router_processos)
app.include_router(execucoes.router)
app.include_router(logs.router_execucoes)
app.include_router(logs.router)
app.include_router(paginas_extraidas.router_execucoes)
app.include_router(paginas_extraidas.router)
app.include_router(monitoring.router)

# Registrar rotas do frontend (devem ser incluídas após as rotas da API)
app.include_router(frontend.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "toninho.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
