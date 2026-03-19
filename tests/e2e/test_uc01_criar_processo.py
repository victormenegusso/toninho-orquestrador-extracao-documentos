"""Testes E2E do UC-01: criar processo com formulario Alpine.js."""

import re
from datetime import datetime, timedelta

import pytest
from playwright.sync_api import Page, expect


def _fill_config_basica(page: Page) -> None:
    page.locator("#urls").fill("https://example.com\nhttps://example.org")
    page.locator("#timeout").fill("120")
    page.locator("#max_retries").fill("2")


@pytest.mark.e2e
class TestCriarProcesso:
    """Cobre criacao de processo e variacoes de configuracao."""

    def test_criar_processo_com_config_completa(self, page: Page) -> None:
        nome = "Processo E2E UC01 Basico"
        descricao = "Descricao UC01"

        page.goto("/processos/novo")
        page.locator("#nome").fill(nome)
        page.locator("#descricao").fill(descricao)
        _fill_config_basica(page)

        page.locator("button:has-text('Criar Processo')").click()

        page.wait_for_url(re.compile(r".*/processos/[0-9a-f-]{36}$"))
        expect(page.locator("main h1")).to_contain_text(nome)
        expect(page.locator("p.text-gray-600.mt-1")).to_contain_text(descricao)
        expect(page.locator("text=2 URL(s)")).to_be_visible()

    def test_criar_processo_com_agendamento_recorrente(self, page: Page) -> None:
        nome = "Processo E2E UC01 Recorrente"

        page.goto("/processos/novo")
        page.locator("#nome").fill(nome)
        _fill_config_basica(page)
        page.locator("#agendamento_tipo").select_option("recorrente")
        page.locator("#agendamento_cron").fill("0 */6 * * *")

        page.locator("button:has-text('Criar Processo')").click()

        page.wait_for_url(re.compile(r".*/processos/[0-9a-f-]{36}$"))
        expect(page.locator("main h1")).to_contain_text(nome)
        expect(page.locator("code")).to_contain_text("0 */6 * * *")

    def test_criar_processo_com_agendamento_one_time(self, page: Page) -> None:
        nome = "Processo E2E UC01 OneTime"
        dt = (datetime.now() + timedelta(days=1)).replace(second=0, microsecond=0)

        page.goto("/processos/novo")
        page.locator("#nome").fill(nome)
        _fill_config_basica(page)
        page.locator("#agendamento_tipo").select_option("one_time")
        page.locator("#agendamento_datetime").fill(dt.strftime("%Y-%m-%dT%H:%M"))

        page.locator("button:has-text('Criar Processo')").click()

        page.wait_for_url(re.compile(r".*/processos/[0-9a-f-]{36}$"))
        expect(page.locator("main h1")).to_contain_text(nome)
        expect(page.locator("text=One Time")).to_be_visible()

    def test_alerta_docling_aparece(self, page: Page) -> None:
        page.goto("/processos/novo")
        page.locator("select[x-model='config.metodo_extracao']").select_option(
            "docling"
        )
        expect(
            page.locator(
                "text=O Docling não suporta páginas que dependem de JavaScript"
            )
        ).to_be_visible()

    def test_criar_processo_com_use_browser(self, page: Page) -> None:
        nome = "Processo E2E UC01 Browser"

        page.goto("/processos/novo")
        page.locator("#nome").fill(nome)
        _fill_config_basica(page)
        page.locator("input[x-model='config.use_browser']").check()

        page.locator("button:has-text('Criar Processo')").click()

        page.wait_for_url(re.compile(r".*/processos/[0-9a-f-]{36}$"))
        expect(page.locator("main h1")).to_contain_text(nome)
        expect(page.locator("text=Usar Navegador")).to_be_visible()
        expect(page.locator("text=Sim")).to_be_visible()
