"""Testes E2E do UC-02: validacao de formulario Alpine.js."""

import pytest
from playwright.sync_api import Page, expect


def _fill_campos_minimos(page: Page, nome: str = "Processo Validacao") -> None:
    page.locator("#nome").fill(nome)
    page.locator("#urls").fill("https://example.com")


@pytest.mark.e2e
class TestValidacaoFormulario:
    """Valida regras client-side e erros server-side do formulario."""

    def test_nome_vazio_exibe_erro_e_nao_envia_requisicao(self, page: Page) -> None:
        requests_processo = []

        def _capture(req) -> None:
            if req.method == "POST" and req.url.endswith("/api/v1/processos"):
                requests_processo.append(req)

        page.on("request", _capture)

        page.goto("/processos/novo")
        page.locator("button:has-text('Criar Processo')").click()

        expect(
            page.locator("p.text-red-600:has-text('Nome é obrigatório.')")
        ).to_be_visible()
        assert len(requests_processo) == 0

    def test_urls_vazias_exibe_erro_inline(self, page: Page) -> None:
        page.goto("/processos/novo")
        page.locator("#nome").fill("Processo Sem URLs")
        page.locator("button:has-text('Criar Processo')").click()

        expect(
            page.locator("p.text-red-600:has-text('Informe ao menos uma URL.')")
        ).to_be_visible()

    def test_timeout_fora_do_range_exibe_erro(self, page: Page) -> None:
        page.goto("/processos/novo")
        _fill_campos_minimos(page, nome="Processo Timeout")
        page.locator("#timeout").fill("0")

        page.locator("button:has-text('Criar Processo')").click()

        expect(
            page.locator(
                "p.text-red-600:has-text('Timeout deve estar entre 1 e 86400.')"
            )
        ).to_be_visible()

    def test_cron_invalido_exibe_erro(self, page: Page) -> None:
        page.goto("/processos/novo")
        _fill_campos_minimos(page, nome="Processo Cron")
        page.locator("#agendamento_tipo").select_option("recorrente")
        page.locator("#agendamento_cron").fill("abc")

        page.locator("button:has-text('Criar Processo')").click()

        expect(page.locator("div[x-show='globalError']")).to_be_visible()
        expect(page.locator("div[x-show='globalError']")).to_contain_text(
            "Revise os campos"
        )
        expect(page.locator("p[x-text='errors.agendamento_cron']")).to_contain_text(
            "Expressão cron"
        )

    def test_nome_duplicado_exibe_global_error(
        self, page: Page, create_processo
    ) -> None:
        processo = create_processo(nome="Processo Duplicado E2E")

        page.goto("/processos/novo")
        _fill_campos_minimos(page, nome=processo["nome"])

        with page.expect_response("**/api/v1/processos") as response_info:
            page.locator("button:has-text('Criar Processo')").click()

        assert response_info.value.status == 409
        expect(page.locator("div[x-show='globalError']")).to_be_visible()
        expect(page.locator("div[x-show='globalError']")).to_contain_text(
            "Já existe um processo com o nome"
        )
