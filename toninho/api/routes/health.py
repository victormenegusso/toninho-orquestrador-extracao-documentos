"""Rota de health check da API."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint para Docker e monitoramento."""
    return {"status": "healthy", "service": "toninho"}


@router.get("/info", summary="Informações da API")
async def api_info():
    """Informações básicas da API."""
    return {
        "name": "Toninho",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }
