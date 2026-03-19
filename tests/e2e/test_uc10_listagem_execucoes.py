"""Testes E2E do UC-10: listagem e filtros de execucoes."""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestListagemExecucoes:
    """Valida tabela de execucoes, badges e filtros por status."""

    def test_tabela_execucoes_exibe_colunas(self, page: Page, create_execucao) -> None:
        create_execucao()

        page.goto("/execucoes")

        expect(page.locator("table")).to_be_visible()
        expect(page.locator("thead")).to_contain_text("ID")
        expect(page.locator("thead")).to_contain_text("Status")
        expect(page.locator("thead")).to_contain_text("Páginas")
        expect(page.locator("thead")).to_contain_text("Taxa Erro")
        expect(page.locator("thead")).to_contain_text("Início")
        expect(page.locator("thead")).to_contain_text("Duração")

    def test_badges_de_status(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        em_execucao = create_execucao()
        concluida = create_execucao()
        falhou = create_execucao()

        update_execucao_status(em_execucao["id"], "em_execucao")
        update_execucao_status(concluida["id"], "em_execucao")
        update_execucao_status(concluida["id"], "concluido")
        update_execucao_status(falhou["id"], "em_execucao")
        update_execucao_status(falhou["id"], "falhou")

        page.goto("/execucoes")

        expect(page.locator(".bg-blue-100.text-blue-800").first).to_be_visible()
        expect(page.locator(".bg-green-100.text-green-800").first).to_be_visible()
        expect(page.locator(".bg-red-100.text-red-800").first).to_be_visible()

    def test_filtro_por_status_na_url(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        em_execucao = create_execucao()
        pausada = create_execucao()

        update_execucao_status(em_execucao["id"], "em_execucao")
        update_execucao_status(pausada["id"], "em_execucao")
        update_execucao_status(pausada["id"], "pausado")

        page.goto("/execucoes?status=em_execucao")

        expect(page).to_have_url(re.compile(r".*/execucoes\?status=em_execucao$"))
        expect(
            page.locator(f"a[href='/execucoes/{em_execucao['id']}']")
        ).to_be_visible()
        expect(page.locator(f"a[href='/execucoes/{pausada['id']}']")).to_have_count(0)

    def test_link_ver_detalhes_funciona(self, page: Page, create_execucao) -> None:
        execucao = create_execucao()

        page.goto("/execucoes")
        page.locator(f"a[href='/execucoes/{execucao['id']}']").click()

        page.wait_for_url(f"**/execucoes/{execucao['id']}")
        expect(page.locator("main h1")).to_contain_text("Execução")
