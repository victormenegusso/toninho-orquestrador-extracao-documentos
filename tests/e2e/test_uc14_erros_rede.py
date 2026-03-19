"""Testes E2E do UC-14: resiliência a erros de rede com HTMX."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestErrosRede:
    """Valida tratamento de falhas em requests HTMX e polling."""

    def test_erro_500_na_busca_nao_limpa_tabela(
        self, page: Page, create_processo
    ) -> None:
        create_processo(nome="Processo Rede 1")
        create_processo(nome="Processo Rede 2")

        page.goto("/processos")
        table = page.locator("#processos-table")
        initial_html = table.inner_html()
        assert len(initial_html.strip()) > 0

        page.route(
            "**/processos/search**",
            lambda route: route.fulfill(status=500, body="Internal Server Error"),
        )

        search = page.locator("input[name='search']")
        search.click()
        page.keyboard.type("rede")
        page.wait_for_timeout(1200)

        current_html = table.inner_html()
        assert len(current_html.strip()) > 0
        expect(table).to_contain_text("Processo Rede")
        page.unroute("**/processos/search**")

    def test_evento_htmx_response_error_disparado(self, page: Page) -> None:
        page.goto("/processos")

        page.evaluate(
            """() => {
                window.__htmxErrors = [];
                document.body.addEventListener('htmx:responseError', (evt) => {
                    window.__htmxErrors.push({
                        status: evt.detail.xhr ? evt.detail.xhr.status : null,
                        path: evt.detail.pathInfo ? evt.detail.pathInfo.requestPath : null,
                    });
                });
            }"""
        )

        page.route(
            "**/processos/search**",
            lambda route: route.fulfill(status=500, body="Internal Server Error"),
        )

        search = page.locator("input[name='search']")
        search.click()
        page.keyboard.type("trigger")
        page.wait_for_timeout(1200)

        errors = page.evaluate("() => window.__htmxErrors")
        assert len(errors) >= 1
        assert any(err.get("status") == 500 for err in errors)
        page.unroute("**/processos/search**")

    def test_polling_dashboard_recupera_apos_falha(self, page: Page) -> None:
        counters = {"ok": 0, "error": 0}
        fail_once = {"done": False}

        def route_polling(route) -> None:
            if not fail_once["done"]:
                fail_once["done"] = True
                route.fulfill(status=500, body="Simulated polling error")
            else:
                route.continue_()

        def count_responses(response) -> None:
            if "/execucoes/ativas" in response.url:
                if response.status >= 500:
                    counters["error"] += 1
                else:
                    counters["ok"] += 1

        page.route("**/execucoes/ativas", route_polling)
        page.on("response", count_responses)

        page.goto("/dashboard")
        expect(page.locator("#execucoes-ativas")).to_be_visible()
        page.wait_for_timeout(11000)

        assert counters["error"] >= 1
        assert counters["ok"] >= 1
        page.unroute("**/execucoes/ativas")
