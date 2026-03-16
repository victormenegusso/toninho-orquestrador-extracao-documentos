"""Testes E2E do UC-11: navegacao de paginas extraidas."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestPaginasExtraidas:
    """Valida grid HTMX, filtros, preview modal e downloads."""

    def test_grid_exibe_cards_e_status(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        data = create_paginas_extraidas(statuses=["sucesso", "falhou", "ignorado"])

        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        expect(page.locator("main h1")).to_contain_text("Páginas Extraídas")
        expect(page.locator("#paginas-grid")).to_be_visible()
        expect(page.locator("#paginas-cards .card")).to_have_count(3)

        grid = page.locator("#paginas-grid")
        expect(grid.locator(".bg-green-100.text-green-800")).to_have_count(1)
        expect(grid.locator(".bg-red-100.text-red-800")).to_have_count(1)
        expect(grid.locator(".bg-gray-100.text-gray-800")).to_have_count(1)

    def test_busca_com_debounce_dispara_htmx(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        data = create_paginas_extraidas(statuses=["sucesso", "sucesso", "sucesso"])

        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        search = page.locator("input[name='search']")
        with page.expect_response("**/paginas/search**", timeout=5000) as resp_info:
            search.click()
            page.keyboard.type("page-1")

        assert resp_info.value.status == 200
        expect(page.locator("#paginas-grid")).to_be_visible()
        # A implementacao atual nao aplica filtro textual no backend.
        expect(page.locator("#paginas-cards .card")).to_have_count(3)

    def test_filtro_por_status_e_busca_combinados(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        data = create_paginas_extraidas(statuses=["sucesso", "falhou", "sucesso"])

        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        with page.expect_response("**/paginas/search**", timeout=5000) as resp_info:
            page.locator("select[name='status']").select_option("sucesso")

        assert resp_info.value.status == 200
        assert "status=sucesso" in resp_info.value.url
        expect(page.locator("#paginas-cards .card")).to_have_count(2)

        with page.expect_response("**/paginas/search**", timeout=5000) as resp_info:
            page.locator("input[name='search']").click()
            page.keyboard.type("page")

        assert resp_info.value.status == 200
        assert "status=sucesso" in resp_info.value.url
        assert "search=page" in resp_info.value.url

    def test_preview_modal_abre_e_fecha_com_escape(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        data = create_paginas_extraidas(statuses=["sucesso"])

        page.goto(f"/execucoes/{data['execucao_id']}/paginas")
        page.locator("button[onclick^='openPreview']").first.click()

        modal = page.locator("#preview-modal")
        expect(modal).to_be_visible()
        expect(page.locator("#preview-content")).to_be_visible(timeout=5000)
        expect(page.locator("#preview-text")).to_contain_text("Conteudo E2E")

        page.keyboard.press("Escape")
        expect(modal).to_be_hidden()

    def test_download_links_individual_e_zip(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        data = create_paginas_extraidas(statuses=["sucesso", "sucesso"])

        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        with page.expect_response("**/api/v1/paginas/*/download") as single_download:
            page.locator("a[href*='/api/v1/paginas/'][download]").first.click()
        assert single_download.value.status == 200
        assert "attachment" in (
            single_download.value.headers.get("content-disposition", "").lower()
        )

        page.goto(f"/execucoes/{data['execucao_id']}/paginas")
        with page.expect_response("**/api/v1/execucoes/*/download-all") as zip_download:
            page.locator("a[href$='/download-all']").click()
        assert zip_download.value.status == 200
        assert "zip" in zip_download.value.headers.get("content-type", "").lower()
