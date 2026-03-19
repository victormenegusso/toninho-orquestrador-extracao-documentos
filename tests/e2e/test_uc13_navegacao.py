"""Testes E2E do UC-13: navegacao geral e sidebar."""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestNavegacaoSidebar:
    """Valida links da sidebar e navegacao com hx-boost."""

    def test_sidebar_exibe_links_e_logo(self, page: Page) -> None:
        page.goto("/dashboard")

        sidebar = page.locator("aside")
        expect(sidebar).to_be_visible()
        expect(sidebar.locator("h1")).to_contain_text("Toninho")
        expect(sidebar.locator("a[href='/dashboard']")).to_be_visible()
        expect(sidebar.locator("a[href='/processos']")).to_be_visible()
        expect(sidebar.locator("a[href='/execucoes']")).to_be_visible()

    def test_navega_entre_rotas_pela_sidebar(self, page: Page) -> None:
        page.goto("/dashboard")

        page.locator("aside a[href='/processos']").click()
        expect(page).to_have_url(re.compile(r".*/processos$"))
        expect(page.locator("main h1")).to_contain_text("Processos")

        page.locator("aside a[href='/execucoes']").click()
        expect(page).to_have_url(re.compile(r".*/execucoes$"))
        expect(page.locator("main h1")).to_contain_text("Execuções")

        page.locator("aside a[href='/dashboard']").click()
        expect(page).to_have_url(re.compile(r".*/dashboard$"))
        expect(page.locator("main h1")).to_contain_text("Dashboard")

    def test_link_sidebar_envia_hx_request(self, page: Page) -> None:
        captured_headers: list[dict[str, str]] = []

        def capture_request(req) -> None:
            if req.method == "GET" and req.url.endswith("/processos"):
                captured_headers.append(req.headers)

        page.on("request", capture_request)
        page.goto("/dashboard")
        page.locator("aside a[href='/processos']").click()

        expect(page).to_have_url(re.compile(r".*/processos$"))
        assert any(h.get("hx-request") == "true" for h in captured_headers)
