"""Testes para as rotas de monitoramento."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from toninho.core.database import get_db
from toninho.main import app


@pytest.fixture
def client(test_engine):
    """FastAPI TestClient com db sobrescrito para testes."""
    from sqlalchemy.orm import sessionmaker

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestHealthRoutes:
    """Testes para os endpoints de health check."""

    def test_health_live(self, client: TestClient):
        """GET /health/live sempre retorna 200."""
        response = client.get("/api/v1/monitoring/health/live")

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_health_check(self, client: TestClient):
        """GET /health retorna health check completo."""
        response = client.get("/api/v1/monitoring/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "database" in data["checks"]

    def test_health_check_db_healthy(self, client: TestClient):
        """GET /health retorna database healthy."""
        response = client.get("/api/v1/monitoring/health")
        data = response.json()

        assert data["status"] in ("healthy", "degraded")
        assert data["checks"]["database"]["status"] == "healthy"

    def test_readiness_healthy(self, client: TestClient):
        """GET /health/ready retorna 200 quando sistema está pronto."""
        response = client.get("/api/v1/monitoring/health/ready")

        assert response.status_code == 200

    def test_readiness_unhealthy_returns_503(self, client: TestClient):
        """GET /health/ready retorna 503 quando sistema não está pronto."""
        with patch(
            "toninho.monitoring.health.HealthCheckService.check_all",
            return_value={
                "status": "unhealthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "checks": {"database": {"status": "unhealthy", "error": "DB down"}},
            },
        ):
            response = client.get("/api/v1/monitoring/health/ready")

        assert response.status_code == 503
        assert response.json()["status"] == "unhealthy"


class TestMetricsRoutes:
    """Testes para os endpoints de métricas."""

    def test_get_metrics(self, client: TestClient):
        """GET /metrics retorna estrutura completa."""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200
        data = response.json()

        assert "executions" in data
        assert "processes" in data
        assert "success_rate" in data
        assert "avg_duration_minutes" in data
        assert "recent_activity" in data

    def test_metrics_executions_structure(self, client: TestClient):
        """Estrutura de execuções contém campos esperados."""
        response = client.get("/api/v1/monitoring/metrics")
        data = response.json()

        exec_data = data["executions"]
        assert "total" in exec_data
        assert "active" in exec_data
        assert "completed" in exec_data
        assert "failed" in exec_data
        assert "pending" in exec_data

    def test_metrics_processes_structure(self, client: TestClient):
        """Estrutura de processos contém campos esperados."""
        response = client.get("/api/v1/monitoring/metrics")
        data = response.json()

        proc_data = data["processes"]
        assert "total" in proc_data
        assert "with_schedule" in proc_data

    def test_metrics_recent_activity_is_list(self, client: TestClient):
        """Atividade recente retorna lista."""
        response = client.get("/api/v1/monitoring/metrics")
        data = response.json()

        assert isinstance(data["recent_activity"], list)
