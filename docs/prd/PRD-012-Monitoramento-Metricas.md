# PRD-012: Monitoramento e Métricas

**Status**: ✅ Concluído
**Prioridade**: 🟡 Média - Backend Features Avançadas (Prioridade 3)
**Categoria**: Backend - Features Avançadas
**Estimativa**: 6-8 horas

---

## 1. Objetivo

Implementar sistema de monitoramento em tempo real, health checks e métricas operacionais. Inclui endpoints de saúde (/health), WebSockets/SSE para atualizações em tempo real, dashboard de métricas e integração com Flower para monitorar Celery.

## 2. Contexto e Justificativa

Monitoramento é essencial para:
- **Observability**: Saber status de workers e execuções
- **Debug**: Identificar problemas rapidamente
- **Ops**: Health checks para loadbalancers/Kubernetes
- **Real-time**: Atualizações ao vivo no frontend

**Features:**
- Health checks (API, workers, Redis, database)
- WebSockets para updates em tempo real
- Métricas agregadas (execuções ativas, taxa de sucesso, etc)
- Flower UI para Celery
- Prometheus metrics (futuro)

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
toninho/monitoring/
├── __init__.py
├── health.py          # Health check handlers
├── metrics.py         # Calculador de métricas
├── websocket.py       # WebSocket manager
└── routes.py          # Rotas de monitoramento

toninho/api/v1/monitoring.py  # API endpoints monitoramento
```

### 3.2. Health Checks (toninho/monitoring/health.py)

**Health check service:**
```python
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from celery import Celery
from redis import Redis
from loguru import logger
import time

class HealthCheckService:
    """Serviço de health checks"""

    def __init__(
        self,
        db_session: AsyncSession,
        celery_app: Celery,
        redis_client: Redis
    ):
        self.db = db_session
        self.celery = celery_app
        self.redis = redis_client

    async def check_all(self) -> Dict[str, any]:
        """
        Executa todos os health checks

        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "timestamp": ISO timestamp,
                "checks": {
                    "database": {...},
                    "redis": {...},
                    "celery_workers": {...}
                }
            }
        """
        checks = {}

        # Database check
        checks["database"] = await self._check_database()

        # Redis check
        checks["redis"] = self._check_redis()

        # Celery workers
        checks["celery_workers"] = self._check_celery_workers()

        # Overall status
        all_healthy = all(c["status"] == "healthy" for c in checks.values())
        any_unhealthy = any(c["status"] == "unhealthy" for c in checks.values())

        if all_healthy:
            overall_status = "healthy"
        elif any_unhealthy:
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }

    async def _check_database(self) -> Dict[str, any]:
        """Verifica conexão com database"""
        try:
            start = time.time()

            # Simple query
            result = await self.db.execute(text("SELECT 1"))
            result.scalar()

            latency = (time.time() - start) * 1000  # ms

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _check_redis(self) -> Dict[str, any]:
        """Verifica conexão com Redis"""
        try:
            start = time.time()

            # Ping Redis
            self.redis.ping()

            latency = (time.time() - start) * 1000  # ms

            # Redis info
            info = self.redis.info()

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _check_celery_workers(self) -> Dict[str, any]:
        """Verifica workers Celery"""
        try:
            # Inspect active workers
            inspect = self.celery.control.inspect()

            stats = inspect.stats()
            active = inspect.active()

            if not stats:
                return {
                    "status": "unhealthy",
                    "error": "No workers available"
                }

            worker_count = len(stats)
            active_tasks = sum(len(tasks) for tasks in active.values()) if active else 0

            return {
                "status": "healthy",
                "worker_count": worker_count,
                "active_tasks": active_tasks,
                "workers": list(stats.keys())
            }

        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
```

### 3.3. Metrics Service (toninho/monitoring/metrics.py)

**Calculador de métricas:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from toninho.models import Execucao, Processo, Log
from toninho.models.enums import ExecucaoStatus
from typing import Dict

class MetricsService:
    """Serviço de cálculo de métricas"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_metrics(self) -> Dict[str, any]:
        """
        Métricas para dashboard

        Returns:
            {
                "executions": {
                    "total": int,
                    "active": int,
                    "completed": int,
                    "failed": int,
                    "pending": int
                },
                "processes": {
                    "total": int,
                    "with_schedule": int
                },
                "success_rate": float,
                "avg_duration_minutes": float,
                "recent_activity": [...]
            }
        """

        # Executions count by status
        exec_counts = await self._count_executions_by_status()

        # Processes count
        process_count = await self._count_processes()

        # Success rate
        success_rate = await self._calculate_success_rate()

        # Average duration
        avg_duration = await self._calculate_avg_duration()

        # Recent activity (últimas 10 execuções)
        recent = await self._get_recent_activity(limit=10)

        return {
            "executions": exec_counts,
            "processes": process_count,
            "success_rate": success_rate,
            "avg_duration_minutes": avg_duration,
            "recent_activity": recent
        }

    async def _count_executions_by_status(self) -> Dict[str, int]:
        """Conta execuções por status"""
        query = select(
            Execucao.status,
            func.count(Execucao.id).label("count")
        ).group_by(Execucao.status)

        result = await self.db.execute(query)
        counts = {row.status.value: row.count for row in result}

        # Active = AGUARDANDO + EM_EXECUCAO + PAUSADO
        active_statuses = [
            ExecucaoStatus.AGUARDANDO.value,
            ExecucaoStatus.EM_EXECUCAO.value,
            ExecucaoStatus.PAUSADO.value
        ]

        return {
            "total": sum(counts.values()),
            "active": sum(counts.get(s, 0) for s in active_statuses),
            "completed": counts.get(ExecucaoStatus.CONCLUIDO.value, 0),
            "failed": counts.get(ExecucaoStatus.ERRO.value, 0),
            "pending": counts.get(ExecucaoStatus.AGUARDANDO.value, 0)
        }

    async def _count_processes(self) -> Dict[str, int]:
        """Conta processos"""
        total_query = select(func.count(Processo.id))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()

        scheduled_query = select(func.count(Processo.id)).where(
            Processo.agendamento.isnot(None)
        )
        scheduled_result = await self.db.execute(scheduled_query)
        scheduled = scheduled_result.scalar()

        return {
            "total": total,
            "with_schedule": scheduled
        }

    async def _calculate_success_rate(self, last_n: int = 100) -> float:
        """Calcula taxa de sucesso das últimas N execuções"""
        query = select(Execucao.status).order_by(
            Execucao.created_at.desc()
        ).limit(last_n)

        result = await self.db.execute(query)
        statuses = [row[0] for row in result]

        if not statuses:
            return 0.0

        succeeded = sum(1 for s in statuses if s == ExecucaoStatus.CONCLUIDO)
        rate = (succeeded / len(statuses)) * 100

        return round(rate, 2)

    async def _calculate_avg_duration(self) -> float:
        """Calcula duração média de execuções concluídas (em minutos)"""
        query = select(
            func.avg(
                func.extract('epoch', Execucao.finished_at - Execucao.started_at)
            )
        ).where(
            Execucao.status == ExecucaoStatus.CONCLUIDO,
            Execucao.finished_at.isnot(None),
            Execucao.started_at.isnot(None)
        )

        result = await self.db.execute(query)
        avg_seconds = result.scalar()

        if not avg_seconds:
            return 0.0

        return round(avg_seconds / 60, 2)

    async def _get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Últimas atividades"""
        query = select(Execucao).order_by(
            Execucao.created_at.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        execucoes = result.scalars().all()

        return [
            {
                "id": str(exec.id),
                "processo_nome": exec.processo.nome if exec.processo else "N/A",
                "status": exec.status.value,
                "created_at": exec.created_at.isoformat()
            }
            for exec in execucoes
        ]
```

### 3.4. WebSocket Manager (toninho/monitoring/websocket.py)

**WebSocket manager para real-time updates:**
```python
from fastapi import WebSocket
from typing import Dict, Set
import json
from loguru import logger

class WebSocketManager:
    """Gerencia WebSocket connections para real-time updates"""

    def __init__(self):
        # Connections por execução
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Connections globais (dashboard)
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, execucao_id: str = None):
        """Adiciona nova conexão"""
        await websocket.accept()

        if execucao_id:
            if execucao_id not in self.active_connections:
                self.active_connections[execucao_id] = set()
            self.active_connections[execucao_id].add(websocket)
            logger.info(f"WebSocket connected for execucao {execucao_id}")
        else:
            self.global_connections.add(websocket)
            logger.info("WebSocket connected to global channel")

    def disconnect(self, websocket: WebSocket, execucao_id: str = None):
        """Remove conexão"""
        if execucao_id:
            if execucao_id in self.active_connections:
                self.active_connections[execucao_id].discard(websocket)
                if not self.active_connections[execucao_id]:
                    del self.active_connections[execucao_id]
        else:
            self.global_connections.discard(websocket)

    async def broadcast_to_execucao(self, execucao_id: str, message: Dict):
        """
        Envia mensagem para todos conectados a uma execução
        """
        if execucao_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[execucao_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.add(connection)

        # Remove disconnected
        for conn in disconnected:
            self.disconnect(conn, execucao_id)

    async def broadcast_global(self, message: Dict):
        """Envia mensagem para todas conexões globais"""
        disconnected = set()

        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.add(connection)

        # Remove disconnected
        for conn in disconnected:
            self.disconnect(conn)

# Singleton
ws_manager = WebSocketManager()
```

### 3.5. API Routes (toninho/api/v1/monitoring.py)

**Endpoints de monitoramento:**
```python
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from toninho.monitoring.health import HealthCheckService
from toninho.monitoring.metrics import MetricsService
from toninho.monitoring.websocket import ws_manager
from toninho.database import get_db

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# Health Check
@router.get("/health", summary="Health check completo")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Verifica saúde de todos os componentes:
    - Database
    - Redis
    - Celery Workers
    """
    health_service = HealthCheckService(db, celery_app, redis_client)
    return await health_service.check_all()

@router.get("/health/live", summary="Liveness probe")
async def liveness():
    """Liveness probe (retorna 200 se API está up)"""
    return {"status": "alive"}

@router.get("/health/ready", summary="Readiness probe")
async def readiness(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe (retorna 200 se pronto para receber tráfego)
    Verifica database + redis
    """
    health_service = HealthCheckService(db, celery_app, redis_client)
    checks = await health_service.check_all()

    if checks["status"] == "unhealthy":
        return JSONResponse(
            status_code=503,
            content=checks
        )

    return checks

# Metrics
@router.get("/metrics", summary="Métricas do sistema")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Retorna métricas agregadas:
    - Contadores de execuções por status
    - Taxa de sucesso
    - Duração média
    - Atividade recente
    """
    metrics_service = MetricsService(db)
    return await metrics_service.get_dashboard_metrics()

# WebSocket para updates em tempo real
@router.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """
    WebSocket para atualizações globais do dashboard

    Envia mensagens:
    {
        "type": "execution_update",
        "data": {...}
    }
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive e recebe mensagens
            data = await websocket.receive_text()
            # Echo (ou processar comandos)
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@router.websocket("/ws/execucao/{execucao_id}")
async def websocket_execucao(websocket: WebSocket, execucao_id: str):
    """
    WebSocket para atualizações de uma execução específica

    Envia:
    - Status updates
    - Progress updates
    - Novos logs
    """
    await ws_manager.connect(websocket, execucao_id)

    try:
        while True:
            data = await websocket.receive_text()
            # Processar comandos do cliente se necessário
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, execucao_id)
```

### 3.6. Integração com Workers

**No worker, emitir updates via WebSocket:**
```python
# No ExtractionOrchestrator ou em tasks Celery
from toninho.monitoring.websocket import ws_manager

async def atualizar_status(execucao_id: str, novo_status: str):
    # Atualizar DB
    ...

    # Broadcast via WebSocket
    await ws_manager.broadcast_to_execucao(
        execucao_id,
        {
            "type": "status_update",
            "data": {
                "status": novo_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

    # Broadcast global
    await ws_manager.broadcast_global({
        "type": "execution_update",
        "data": {
            "execucao_id": execucao_id,
            "status": novo_status
        }
    })
```

## 4. Dependências

### 4.1. Bibliotecas
- fastapi: ^0.109.0 (WebSocket support)
- celery: ^5.3.6
- redis: ^5.0.1
- loguru: ^0.7.2

### 4.2. Dependências de Outros PRDs
- PRD-003: Models (Execucao, Processo, Log)
- PRD-010: Workers (integração com Celery)

## 5. Regras de Negócio

### 5.1. Health Checks
- `/health`: Retorna status de todos os componentes
- `/health/live`: Sempre 200 OK (liveness probe)
- `/health/ready`: 503 se unhealthy (readiness probe)

### 5.2. Status
- `healthy`: Todos os componentes OK
- `degraded`: Alguns componentes com problemas não críticos
- `unhealthy`: Componentes críticos indisponíveis

### 5.3. WebSocket
- Conexões globais: Recebem updates de todas execuções
- Conexões por execução: Recebem apenas updates daquela execução
- Reconexão automática no cliente

### 5.4. Métricas
- Taxa de sucesso: Baseada em últimas 100 execuções
- Duração média: Apenas execuções concluídas
- Atividade recente: Últimas 10 execuções

## 6. Casos de Teste

### 6.1. Health Checks
- ✅ `/health` retorna status healthy quando tudo OK
- ✅ `/health` retorna unhealthy quando DB offline
- ✅ `/health` retorna degraded quando workers offline
- ✅ `/health/live` sempre retorna 200
- ✅ `/health/ready` retorna 503 quando unhealthy

### 6.2. Metrics
- ✅ Dashboard metrics calcula corretamente
- ✅ Success rate calculado corretamente
- ✅ Average duration calculado corretamente
- ✅ Recent activity retorna últimas 10

### 6.3. WebSocket
- ✅ Conexão WebSocket é aceita
- ✅ Broadcast para execução funciona
- ✅ Broadcast global funciona
- ✅ Disconnect remove conexão da lista

## 7. Critérios de Aceitação

### ✅ Health Checks
- [ ] Endpoint `/health` verifica DB, Redis, Celery
- [ ] Endpoint `/health/live` para liveness
- [ ] Endpoint `/health/ready` para readiness
- [ ] Status correto retornado

### ✅ Metrics
- [ ] Dashboard metrics endpoint
- [ ] Métricas calculadas corretamente
- [ ] Performance aceitável (< 500ms)

### ✅ WebSocket
- [ ] WebSocket global funciona
- [ ] WebSocket por execução funciona
- [ ] Broadcast envia mensagens
- [ ] Handles disconnect

### ✅ Integração
- [ ] Workers emitem updates via WebSocket
- [ ] Frontend pode conectar e receber updates

### ✅ Testes
- [ ] Testes com cobertura > 80%

## 8. Notas de Implementação

### 8.1. Flower UI
Flower já configurado no docker-compose.yml:
```yaml
flower:
  image: mher/flower
  command: celery --broker=redis://redis:6379/0 flower --port=5555
  ports:
    - "5555:5555"
```

Acessível em: http://localhost:5555

### 8.2. Prometheus/Grafana (Futuro)
Para produção, adicionar:
- prometheus-fastapi-instrumentator
- Métricas expostas em `/metrics` (Prometheus format)
- Grafana dashboard

### 8.3. Alerting (Futuro)
- Alertas quando workers offline
- Alertas quando taxa de erro > threshold
- Integração com Sentry para error tracking

### 8.4. WebSocket vs SSE
- WebSocket: Bidirecional, usado aqui
- SSE (Server-Sent Events): Unidirecional, alternativa mais simples
- Frontend pode usar ambos

## 9. Referências Técnicas

- **FastAPI WebSocket**: https://fastapi.tiangolo.com/advanced/websockets/
- **Flower**: https://flower.readthedocs.io/
- **Prometheus FastAPI**: https://github.com/trallnag/prometheus-fastapi-instrumentator

## 10. Definição de Pronto

- ✅ Health check endpoints implementados
- ✅ Metrics service calcula métricas
- ✅ WebSocket manager funciona
- ✅ Workers emitem updates em tempo real
- ✅ Flower configurado e acessível
- ✅ Testes com cobertura > 80%
- ✅ Documentação de uso dos endpoints

---

**PRD Anterior**: PRD-011 - Sistema de Extração
**Próximo PRD**: PRD-013 - Testes e Qualidade
