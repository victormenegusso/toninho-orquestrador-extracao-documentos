"""
Testes de integração para o Frontend (PRD-014).

Testa as rotas HTML que servem os templates Jinja2.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Fixture que retorna um cliente de teste da aplicação."""
    from toninho.main import app

    return TestClient(app, raise_server_exceptions=True)


class TestFrontendSetup:
    """Testes de setup do frontend - PRD-014."""

    def test_home_page_retorna_html(self, client):
        """GET / deve retornar página HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_home_page_conteudo(self, client):
        """Página home deve conter elementos esperados."""
        response = client.get("/")
        html = response.text
        assert "Toninho" in html
        assert "Dashboard" in html

    def test_dashboard_page_retorna_html(self, client):
        """GET /dashboard deve retornar página HTML."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_conteudo(self, client):
        """Dashboard deve conter elementos esperados."""
        response = client.get("/dashboard")
        html = response.text
        assert "Dashboard" in html
        assert "Toninho" in html

    def test_dashboard_tem_sidebar(self, client):
        """Dashboard deve incluir sidebar com links de navegação."""
        response = client.get("/dashboard")
        html = response.text
        assert "Processos" in html
        assert "Execuções" in html

    def test_dashboard_tem_stats_cards(self, client):
        """Dashboard deve exibir cards de estatísticas."""
        response = client.get("/dashboard")
        html = response.text
        assert "Total Processos" in html
        assert "Processos Ativos" in html

    def test_dashboard_tem_acoes_rapidas(self, client):
        """Dashboard deve ter seção de ações rápidas."""
        response = client.get("/dashboard")
        html = response.text
        assert "Ações Rápidas" in html
        assert "Novo Processo" in html

    def test_html_tem_htmx(self, client):
        """Templates devem incluir HTMX."""
        response = client.get("/")
        html = response.text
        assert "htmx" in html.lower()

    def test_html_tem_alpinejs(self, client):
        """Templates devem incluir Alpine.js."""
        response = client.get("/")
        html = response.text
        assert "alpinejs" in html.lower() or "alpine" in html.lower()

    def test_html_tem_tailwind(self, client):
        """Templates devem incluir Tailwind CSS."""
        response = client.get("/")
        html = response.text
        assert "tailwindcss" in html.lower() or "tailwind" in html.lower()

    def test_api_info_endpoint(self, client):
        """GET /api/v1/info deve retornar JSON com informações da API."""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Toninho"
        assert data["version"] == "0.1.0"
        assert data["status"] == "operational"

    def test_health_check(self, client):
        """GET /api/v1/health deve retornar status ok."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestFrontendTemplateContext:
    """Testes do contexto global dos templates."""

    def test_home_tem_versao(self, client):
        """Templates devem exibir versão da aplicação."""
        response = client.get("/")
        html = response.text
        assert "1.0.0" in html

    def test_dashboard_tem_versao(self, client):
        """Dashboard deve exibir versão."""
        response = client.get("/dashboard")
        html = response.text
        # Versão no sidebar ou navbar
        assert "1.0.0" in html or "v1.0" in html

    def test_home_link_para_dashboard(self, client):
        """Página home deve ter link para o dashboard."""
        response = client.get("/")
        html = response.text
        assert 'href="/dashboard"' in html

    def test_home_link_para_docs(self, client):
        """Página home deve ter link para documentação API."""
        response = client.get("/")
        html = response.text
        assert "/docs" in html
