"""Testes E2E do UC-08: logs em tempo real via SSE no detalhe de execucao."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestLogsSSE:
    """Valida conexao SSE, renderizacao de logs e polling de progresso."""

    def test_container_logs_e_mensagem_inicial(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        execucao = create_execucao()
        update_execucao_status(execucao["id"], "em_execucao")

        page.goto(f"/execucoes/{execucao['id']}")

        expect(page.locator("#logs-container")).to_be_visible()
        expect(page.locator("#logs-content")).to_have_count(1)
        expect(page.locator("#auto-scroll")).to_be_checked()
        expect(page.locator("#log-level-filter")).to_be_visible()

    def test_logs_chegam_via_sse(
        self,
        page: Page,
        create_execucao,
        update_execucao_status,
        create_logs_batch,
    ) -> None:
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        create_logs_batch(
            execucao_id,
            [
                {"nivel": "info", "mensagem": "Iniciando extracao"},
                {"nivel": "warning", "mensagem": "Timeout parcial"},
                {"nivel": "error", "mensagem": "Falha ao baixar recurso"},
            ],
        )

        page.goto(f"/execucoes/{execucao_id}")

        expect(page.locator("#logs-content")).to_contain_text(
            "Iniciando extracao", timeout=10000
        )
        expect(page.locator("#logs-content")).to_contain_text(
            "Timeout parcial", timeout=10000
        )
        expect(page.locator("#logs-content")).to_contain_text(
            "Falha ao baixar recurso", timeout=10000
        )

    def test_filtro_logs_reseta_container(
        self,
        page: Page,
        create_execucao,
        update_execucao_status,
        create_logs_batch,
    ) -> None:
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        create_logs_batch(
            execucao_id,
            [{"nivel": "info", "mensagem": "Mensagem para filtro"}],
        )

        page.goto(f"/execucoes/{execucao_id}")
        expect(page.locator("#logs-content")).to_contain_text(
            "Mensagem para filtro", timeout=10000
        )

        page.locator("#log-level-filter").select_option("ERROR")
        expect(page.locator("#logs-content")).to_be_empty()

    def test_progress_polling_a_cada_2s(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        execucao = create_execucao()
        update_execucao_status(execucao["id"], "em_execucao")

        page.goto(f"/execucoes/{execucao['id']}")
        expect(page.locator("#progress-section")).to_be_visible()

        with page.expect_response(
            f"**/execucoes/{execucao['id']}/progress", timeout=5000
        ) as resp_info:
            pass

        assert resp_info.value.status == 200

    def test_stream_encerra_quando_execucao_finaliza(
        self,
        page: Page,
        create_execucao,
        update_execucao_status,
        create_logs_batch,
    ) -> None:
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        create_logs_batch(
            execucao_id,
            [{"nivel": "info", "mensagem": "Antes de encerrar"}],
        )

        page.goto(f"/execucoes/{execucao_id}")
        expect(page.locator("#logs-content")).to_contain_text(
            "Antes de encerrar", timeout=10000
        )

        update_execucao_status(execucao_id, "concluido")
        page.wait_for_timeout(1500)
        expect(page.locator("#logs-content")).to_contain_text("Antes de encerrar")

        page.reload()
        expect(
            page.locator("div.bg-white.rounded-lg.shadow.p-4").first
        ).to_contain_text("concluido")
