"""
Testes de integração para a API principal.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Fixture que retorna um cliente de teste da API."""
    from toninho.main import app
    return TestClient(app)


def test_root_endpoint(client):
    """Testa o endpoint raiz."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Toninho"
    assert data["version"] == "0.1.0"
    assert data["status"] == "operational"


def test_health_check_endpoint(client):
    """Testa o endpoint de health check."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "toninho"


def test_docs_endpoint(client):
    """Testa se a documentação Swagger está disponível."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint(client):
    """Testa se o schema OpenAPI está disponível."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Toninho - Extrator de Processos"
