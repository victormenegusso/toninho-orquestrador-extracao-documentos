"""Testes E2E do UC-07: dashboard e polling HTMX."""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestDashboardPolling:
    """Valida dashboard, quick actions e polling de execucoes ativas."""

    def test_dashboard_exibe_cards_e_quick_actions(self, page: Page) -> None:
        page.goto("/dashboard")

        expect(page.locator("main h1")).to_contain_text("Dashboard")
        expect(page.locator("text=Total Processos")).to_be_visible()
        expect(page.locator("text=Processos Ativos")).to_be_visible()
        expect(page.locator("text=Execuções Hoje")).to_be_visible()
        expect(page.locator("text=Taxa de Sucesso")).to_be_visible()
        expect(page.locator("a[href='/processos/novo']")).to_be_visible()
        expect(page.locator("a[href='/processos']").first).to_be_visible()
        expect(page.locator("a[href='/execucoes']").first).to_be_visible()
        expect(page.locator("a[href='/docs']").first).to_be_visible()

    def test_cards_exibem_valores_numericos(self, page: Page) -> None:
        page.goto("/dashboard")

        expect(page.locator("text=Total Processos").locator("..")).to_contain_text(
            re.compile(r"\d+")
        )
        expect(page.locator("text=Processos Ativos").locator("..")).to_contain_text(
            re.compile(r"\d+")
        )
        expect(page.locator("text=Execuções Hoje").locator("..")).to_contain_text(
            re.compile(r"\d+")
        )
        expect(page.locator("text=Taxa de Sucesso").locator("..")).to_contain_text(
            re.compile(r"\d+\.?\d*%")
        )

    def test_execucoes_ativas_polling_every_3s(self, page: Page) -> None:
        page.goto("/dashboard")
        expect(page.locator("#execucoes-ativas")).to_be_visible()

        with page.expect_response("**/execucoes/ativas", timeout=5000) as resp_info:
            pass

        assert resp_info.value.status == 200

    def test_dashboard_stats_endpoint_disponivel(
        self, page: Page, base_url: str
    ) -> None:
        response = page.request.get(f"{base_url}/dashboard/stats")
        assert response.status == 200

    def test_quick_action_links_funcionam(self, page: Page) -> None:
        page.goto("/dashboard")

        page.locator("a[href='/processos/novo']").first.click()
        page.wait_for_url("**/processos/novo")
        expect(page).to_have_url(re.compile(r".*/processos/novo$"))

        page.goto("/dashboard")
        page.locator("a[href='/processos']").first.click()
        page.wait_for_url("**/processos")
        expect(page).to_have_url(re.compile(r".*/processos$"))
