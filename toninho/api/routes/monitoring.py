"""Rotas de monitoramento, health checks e métricas."""

from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from toninho.core.database import get_db
from toninho.monitoring.health import HealthCheckService
from toninho.monitoring.metrics import MetricsService
from toninho.monitoring.websocket import ws_manager

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoramento"])


# ─── Health Checks ───────────────────────────────────────────────────────────


@router.get(
    "/health",
    summary="Health check completo",
    description="Verifica saúde de todos os componentes: database, Redis e Celery workers.",
)
def health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retorna status de saúde de todos os componentes."""
    service = HealthCheckService(db=db)
    return service.check_all()


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Liveness probe — retorna 200 se a API está em execução.",
)
def liveness() -> dict[str, str]:
    """Liveness probe: sempre retorna 200 se a API está up."""
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Readiness probe — retorna 503 se o sistema não está pronto para receber tráfego.",
)
def readiness(db: Session = Depends(get_db)):
    """
    Readiness probe: verifica se o sistema está pronto.
    Retorna 503 se unhealthy.
    """
    service = HealthCheckService(db=db)
    result = service.check_all()

    if result["status"] == "unhealthy":
        return JSONResponse(status_code=503, content=result)

    return result


# ─── Metrics ─────────────────────────────────────────────────────────────────


@router.get(
    "/metrics",
    summary="Métricas do sistema",
    description="Retorna métricas agregadas: execuções por status, taxa de sucesso, duração média e atividade recente.",
)
def get_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retorna métricas do dashboard."""
    service = MetricsService(db=db)
    return service.get_dashboard_metrics()


# ─── WebSocket ────────────────────────────────────────────────────────────────


@router.websocket("/ws")
async def websocket_global(websocket: WebSocket) -> None:
    """
    WebSocket para atualizações globais do dashboard.

    Envia mensagens com formato:
        {"type": "execution_update", "data": {...}}
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo — extensível para processar comandos
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/execucao/{execucao_id}")
async def websocket_execucao(websocket: WebSocket, execucao_id: str) -> None:
    """
    WebSocket para atualizações de uma execução específica.

    Envia status updates, progress updates e novos logs.
    """
    await ws_manager.connect(websocket, execucao_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Processar comandos do cliente se necessário
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, execucao_id)
