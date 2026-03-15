"""Teste de smoke para validar infraestrutura E2E com Playwright."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestSmoke:
    """Testes de smoke para validar setup do Playwright no projeto."""

    def test_home_page_loads(self, page: Page) -> None:
        """Pagina inicial deve responder 200."""
        response = page.goto("/")
        assert response is not None
        assert response.status == 200

    def test_home_page_has_title(self, page: Page) -> None:
        """Titulo da pagina inicial deve conter o nome do app."""
        page.goto("/")
        expect(page).to_have_title("Bem-vindo - Extrator de Processos")

    def test_dashboard_loads(self, page: Page) -> None:
        """Dashboard deve carregar conteudo principal."""
        page.goto("/dashboard")
        expect(page.locator("main h1")).to_contain_text("Dashboard")

    def test_htmx_is_loaded(self, page: Page) -> None:
        """HTMX deve estar carregado no browser."""
        page.goto("/dashboard")
        htmx_version = page.evaluate("() => window.htmx && window.htmx.version")
        assert htmx_version is not None

    def test_alpine_is_loaded(self, page: Page) -> None:
        """Alpine.js deve estar disponivel na pagina do formulario."""
        page.goto("/processos/novo")
        page.wait_for_function("() => typeof Alpine !== 'undefined'")

    def test_api_health_from_browser(self, page: Page) -> None:
        """Health check da API deve estar acessivel via navegador."""
        response = page.goto("/api/v1/health")
        assert response is not None
        assert response.status == 200

    def test_static_files_served(self, page: Page) -> None:
        """Pagina deve carregar sem erros de JS em runtime."""
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto("/dashboard")
        page.wait_for_load_state("networkidle")
        assert not errors, f"Erros no console: {errors}"
