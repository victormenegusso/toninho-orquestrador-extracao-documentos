"""Testes E2E do UC-04: busca e filtro de processos via HTMX."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestBuscaProcessos:
    """Valida busca com debounce, filtros e estado vazio na listagem."""

    def test_busca_por_nome_com_debounce(self, page: Page, create_processo) -> None:
        alpha = create_processo(nome="Alpha Processo", status="ativo")
        beta = create_processo(nome="Beta Processo", status="ativo")
        gamma = create_processo(nome="Gamma Processo", status="ativo")

        page.goto("/processos")

        with page.expect_response("**/processos/search*") as resp_info:
            page.locator("input[name='search']").click()
            page.keyboard.type("Alpha")

        assert resp_info.value.status == 200
        expect(page.locator(f"#processo-row-{alpha['id']}")).to_be_visible()
        expect(page.locator(f"#processo-row-{beta['id']}")).to_have_count(0)
        expect(page.locator(f"#processo-row-{gamma['id']}")).to_have_count(0)

    def test_filtro_por_status(self, page: Page, create_processo) -> None:
        ativo = create_processo(nome="Ativo Filtro", status="ativo")
        inativo = create_processo(nome="Inativo Filtro", status="inativo")

        page.goto("/processos")

        with page.expect_response("**/processos/search*") as resp_info:
            page.locator("select[name='status']").select_option("INATIVO")

        assert resp_info.value.status == 200
        expect(page.locator(f"#processo-row-{inativo['id']}")).to_be_visible()
        expect(page.locator(f"#processo-row-{ativo['id']}")).to_be_visible()

    def test_busca_e_filtro_combinados(self, page: Page, create_processo) -> None:
        ativo = create_processo(nome="Cliente A - Ativo", status="ativo")
        inativo_a = create_processo(nome="Cliente A - Inativo", status="inativo")
        inativo_b = create_processo(nome="Cliente B - Inativo", status="inativo")

        page.goto("/processos")

        with page.expect_response("**/processos/search*") as first_resp:
            page.locator("input[name='search']").click()
            page.keyboard.type("Cliente A")
        assert first_resp.value.status == 200

        with page.expect_response("**/processos/search*") as second_resp:
            page.locator("select[name='status']").select_option("INATIVO")
        assert second_resp.value.status == 200

        expect(page.locator(f"#processo-row-{inativo_a['id']}")).to_be_visible()
        expect(page.locator(f"#processo-row-{ativo['id']}")).to_be_visible()
        expect(page.locator(f"#processo-row-{inativo_b['id']}")).to_have_count(0)

    def test_busca_sem_resultados(self, page: Page, create_processo) -> None:
        create_processo(nome="Processo Existente", status="ativo")

        page.goto("/processos")

        with page.expect_response("**/processos/search*") as resp_info:
            page.locator("input[name='search']").click()
            page.keyboard.type("ZZZNAOEXISTE")

        assert resp_info.value.status == 200
        expect(page.locator("#processos-table")).to_contain_text(
            "Nenhum processo encontrado"
        )

    def test_limpar_busca_retorna_lista(self, page: Page, create_processo) -> None:
        alpha = create_processo(nome="Alpha Limpar", status="ativo")
        beta = create_processo(nome="Beta Limpar", status="ativo")

        page.goto("/processos")

        with page.expect_response("**/processos/search*"):
            page.locator("input[name='search']").click()
            page.keyboard.type("Alpha")

        expect(page.locator(f"#processo-row-{alpha['id']}")).to_be_visible()
        expect(page.locator(f"#processo-row-{beta['id']}")).to_have_count(0)

        with page.expect_response("**/processos/search*"):
            page.locator("input[name='search']").fill("")

        expect(page.locator(f"#processo-row-{alpha['id']}")).to_be_visible()
        expect(page.locator(f"#processo-row-{beta['id']}")).to_be_visible()
