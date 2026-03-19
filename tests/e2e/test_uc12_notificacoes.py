"""Testes E2E do UC-12: notificacoes e eventos HTMX."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestNotificacoes:
    """Valida comportamento de alerts Alpine e erros HTMX."""

    def test_alert_flash_fecha_com_alpine(self, page: Page) -> None:
        page.goto("/dashboard")

        page.evaluate(
            """() => {
                const host = document.createElement('div');
                host.id = 'flash-messages';
                host.className = 'fixed top-4 right-4 z-50';
                host.innerHTML = `
                  <div x-data="{ show: true }" x-show="show" class="bg-green-50 text-green-800 rounded-md p-4">
                    <p class="text-sm font-medium">Processo criado com sucesso</p>
                    <button @click="show = false" type="button">Fechar</button>
                  </div>
                `;
                document.body.appendChild(host);
            }"""
        )

        container = page.locator("#flash-messages")
        expect(container).to_be_visible()
        expect(container.locator(".bg-green-50")).to_be_visible()

        container.locator("button").click()
        expect(container.locator(".bg-green-50")).to_be_hidden()

    def test_htmx_response_error_gera_console_error(self, page: Page) -> None:
        errors: list[str] = []

        page.on(
            "console",
            lambda msg: errors.append(msg.text)
            if msg.type == "error" and "HTMX error:" in msg.text
            else None,
        )

        page.goto("/processos")
        page.route(
            "**/processos/search**",
            lambda route: route.fulfill(status=500, body="Internal Server Error"),
        )

        search = page.locator("input[name='search']")
        search.click()
        page.keyboard.type("erro-htmx")
        page.wait_for_timeout(1200)

        assert any("HTMX error:" in msg for msg in errors)
        page.unroute("**/processos/search**")
