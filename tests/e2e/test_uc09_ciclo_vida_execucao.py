"""Testes E2E do UC-09: ciclo de vida de execucao (pausar/retomar/cancelar)."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestCicloVidaExecucao:
    """Valida botoes condicionais e transicoes de status na pagina de detalhe."""

    def test_botoes_visiveis_quando_em_execucao(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        page.goto(f"/execucoes/{execucao_id}")

        expect(page.locator("button:has-text('Pausar')")).to_be_visible()
        expect(page.locator("button:has-text('Cancelar')")).to_be_visible()
        expect(page.locator("button:has-text('Retomar')")).to_have_count(0)

    @staticmethod
    def _status_badge(page: Page):
        return page.locator("div.bg-white.rounded-lg.shadow.p-4").first.locator(
            "span.inline-flex"
        )

    def test_pausar_execucao(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        page.goto(f"/execucoes/{execucao_id}")
        page.once("dialog", lambda dialog: dialog.accept())

        with page.expect_response(
            f"**/api/v1/execucoes/{execucao_id}/pausar"
        ) as resp_info:
            page.locator("button:has-text('Pausar')").click()

        assert resp_info.value.status == 200

        page.reload()
        expect(self._status_badge(page)).to_contain_text("pausado")
        expect(page.locator("button:has-text('Retomar')")).to_be_visible()

    def test_retomar_execucao(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")
        update_execucao_status(execucao_id, "pausado")

        page.goto(f"/execucoes/{execucao_id}")

        with page.expect_response(
            f"**/api/v1/execucoes/{execucao_id}/retomar"
        ) as resp_info:
            page.locator("button:has-text('Retomar')").click()

        assert resp_info.value.status == 200

        page.reload()
        expect(self._status_badge(page)).to_contain_text("em_execucao")
        expect(page.locator("button:has-text('Pausar')")).to_be_visible()

    def test_cancelar_execucao(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        page.goto(f"/execucoes/{execucao_id}")
        page.once("dialog", lambda dialog: dialog.accept())

        with page.expect_response(
            f"**/api/v1/execucoes/{execucao_id}/cancelar"
        ) as resp_info:
            page.locator("button:has-text('Cancelar')").click()

        assert resp_info.value.status == 200

        page.reload()
        expect(self._status_badge(page)).to_contain_text("cancelado")
        expect(page.locator("button:has-text('Pausar')")).to_have_count(0)
        expect(page.locator("button:has-text('Retomar')")).to_have_count(0)
        expect(page.locator("button:has-text('Cancelar')")).to_have_count(0)
