"""Testes E2E do UC-15: campos pré-preenchidos em formulários."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestFormularioPrePreenchido:
    """Verifica que campos default estão presentes ao acessar o formulário."""

    def test_campos_default_via_url_direta(self, page: Page) -> None:
        """Campos default presentes ao acessar /processos/novo diretamente."""
        page.goto("/processos/novo")

        # Process field defaults
        expect(page.locator("#nome")).to_have_value("")
        expect(page.locator("#descricao")).to_have_value("")
        expect(page.locator("#status")).to_have_value("ativo")

        # Configuration field defaults
        expect(page.locator("#urls")).to_have_value("")
        expect(page.locator("#timeout")).to_have_value("3600")
        expect(page.locator("#max_retries")).to_have_value("3")
        expect(page.locator("#formato_saida")).to_have_value("multiplos_arquivos")
        expect(page.locator("#output_dir")).to_have_value("./output")
        expect(page.locator("#agendamento_tipo")).to_have_value("manual")

        # Fields without an id use x-model selectors
        expect(page.locator("select[x-model='config.metodo_extracao']")).to_have_value(
            "html2text"
        )
        expect(page.locator("input[x-model='config.use_browser']")).not_to_be_checked()

    def test_campos_default_via_navegacao_htmx(self, page: Page) -> None:
        """Campos default presentes ao navegar via link (HTMX swap)."""
        page.goto("/processos")

        # Navigate to create form via "Novo Processo" link
        novo_link = page.locator("a[href='/processos/novo']").first
        if novo_link.is_visible():
            novo_link.click()
        else:
            page.goto("/processos/novo")

        page.wait_for_load_state("networkidle")

        expect(page.locator("#timeout")).to_have_value("3600")
        expect(page.locator("#max_retries")).to_have_value("3")
        expect(page.locator("#output_dir")).to_have_value("./output")
        expect(page.locator("#formato_saida")).to_have_value("multiplos_arquivos")
        expect(page.locator("#agendamento_tipo")).to_have_value("manual")
        expect(page.locator("#status")).to_have_value("ativo")

    def test_campos_persistem_apos_navegacao_ida_e_volta(self, page: Page) -> None:
        """Campos default presentes após navegar ida e volta."""
        page.goto("/processos/novo")

        expect(page.locator("#timeout")).to_have_value("3600")
        expect(page.locator("#max_retries")).to_have_value("3")

        # Navigate away
        page.goto("/processos")

        # Navigate back
        page.goto("/processos/novo")

        expect(page.locator("#timeout")).to_have_value("3600")
        expect(page.locator("#max_retries")).to_have_value("3")
        expect(page.locator("#output_dir")).to_have_value("./output")
        expect(page.locator("#formato_saida")).to_have_value("multiplos_arquivos")

    def test_formulario_edicao_carrega_valores_existentes(
        self, page: Page, create_processo_com_config
    ) -> None:
        """Em modo edição, formulário carrega valores do processo existente."""
        processo, config = create_processo_com_config(
            processo_kwargs={"nome": "Processo Pre-preenchido E2E"},
            config_kwargs={
                "urls": ["https://example.com", "https://test.com"],
                "timeout": 120,
                "max_retries": 5,
            },
        )
        processo_id = processo["id"]

        page.goto(f"/processos/{processo_id}/editar")

        expect(page.locator("#nome")).to_have_value("Processo Pre-preenchido E2E")
        expect(page.locator("#timeout")).to_have_value("120")
        expect(page.locator("#max_retries")).to_have_value("5")
