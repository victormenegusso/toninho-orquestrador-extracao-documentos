"""Testes E2E do UC-05: executar processo com confirmacao HTMX."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
class TestExecutarProcesso:
    """Valida fluxo de execucao na listagem e no detalhe do processo."""

    def test_executar_da_listagem_com_confirmacao(
        self, page: Page, create_processo_com_config
    ) -> None:
        processo, _ = create_processo_com_config(
            processo_kwargs={"nome": "Processo Executar Lista"},
            config_kwargs={"urls": ["https://example.com/exec"]},
        )

        page.goto("/processos")
        page.once("dialog", lambda dialog: dialog.accept())

        with page.expect_response(
            f"**/api/v1/processos/{processo['id']}/execucoes"
        ) as resp_info:
            page.locator(
                f"#processo-row-{processo['id']} button[title='Executar agora']"
            ).click()

        assert resp_info.value.status == 201

    def test_cancelar_confirmacao_nao_dispara_requisicao(
        self, page: Page, create_processo_com_config
    ) -> None:
        processo, _ = create_processo_com_config(
            processo_kwargs={"nome": "Processo Executar Cancelar"},
            config_kwargs={"urls": ["https://example.com/cancel"]},
        )
        post_requests: list[str] = []

        def _capture(req) -> None:
            if req.method == "POST" and "/execucoes" in req.url:
                post_requests.append(req.url)

        page.on("request", _capture)
        page.goto("/processos")
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.locator(
            f"#processo-row-{processo['id']} button[title='Executar agora']"
        ).click()
        page.wait_for_timeout(300)

        assert len(post_requests) == 0

    def test_executar_da_pagina_detalhe(
        self, page: Page, create_processo_com_config
    ) -> None:
        processo, _ = create_processo_com_config(
            processo_kwargs={"nome": "Processo Executar Detalhe"},
            config_kwargs={"urls": ["https://example.com/detail"]},
        )

        page.goto(f"/processos/{processo['id']}")
        page.once("dialog", lambda dialog: dialog.accept())

        with page.expect_response(
            f"**/api/v1/processos/{processo['id']}/execucoes"
        ) as resp_info:
            page.locator("button:has-text('Executar Agora')").click()

        assert resp_info.value.status == 201
