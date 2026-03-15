"""Testes E2E do UC-03: edicao de processo com valores pre-carregados."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestEditarProcesso:
    """Valida pre-populacao e persistencia da edicao de processo."""

    def test_editar_processo_com_valores_pre_carregados(
        self, page: Page, create_processo_com_config
    ) -> None:
        processo, _ = create_processo_com_config(
            processo_kwargs={
                "nome": "Processo E2E Editar",
                "descricao": "Descricao original",
            },
            config_kwargs={
                "urls": ["https://example.com/a", "https://example.com/b"],
                "timeout": 180,
                "max_retries": 1,
            },
        )

        page.goto(f"/processos/{processo['id']}/editar")

        expect(page.locator("#nome")).to_have_value("Processo E2E Editar")
        expect(page.locator("#descricao")).to_have_value("Descricao original")
        expect(page.locator("#urls")).to_have_value(
            "https://example.com/a\nhttps://example.com/b"
        )
        expect(page.locator("#timeout")).to_have_value("180")

        page.locator("#nome").fill("Processo Editado E2E")
        page.locator("#timeout").fill("300")

        with page.expect_response(f"**/api/v1/processos/{processo['id']}") as resp_info:
            page.locator("button:has-text('Salvar Alterações')").click()

        assert resp_info.value.status == 200

        page.wait_for_url(f"**/processos/{processo['id']}")
        expect(page.locator("main h1")).to_contain_text("Processo Editado E2E")
        expect(page.locator("text=300s")).to_be_visible()
