"""Testes E2E do UC-06: deletar processo pela listagem HTMX."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestDeletarProcesso:
    """Valida confirmacao de delecao e remocao da linha com swap HTMX."""

    def test_deletar_processo_remove_linha_e_persistencia(
        self, page: Page, create_processo
    ) -> None:
        processo = create_processo(nome="Processo Deletar E2E", status="inativo")
        processo_id = processo["id"]

        page.goto("/processos")
        row = page.locator(f"#processo-row-{processo_id}")
        expect(row).to_be_visible()

        page.once("dialog", lambda dialog: dialog.accept())
        with page.expect_response(f"**/api/v1/processos/{processo_id}") as resp_info:
            row.locator("button[title='Deletar']").click()

        assert resp_info.value.status == 204

        page.reload()
        expect(page.locator("#processos-table")).not_to_contain_text(
            "Processo Deletar E2E"
        )
