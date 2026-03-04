"""
Testes de integração para Interface de Monitoramento (PRD-016).

Testa as rotas HTML de execuções, dashboard com monitoramento em tempo real,
partials de polling (stats, progresso, execuções ativas).
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.enums import ExecucaoStatus
from toninho.models.execucao import Execucao
from toninho.models.processo import Processo


@pytest.fixture
def client(test_engine):
    """Fixture que retorna cliente de teste com banco de dados de teste."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=True)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def execucao_no_db(db):
    """Cria uma execução no banco de dados para testes."""
    processo = Processo(
        nome="Processo para Execução",
        descricao="Processo criado para testes de monitoramento",
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    execucao = Execucao(
        processo_id=processo.id,
        status=ExecucaoStatus.EM_EXECUCAO,
        paginas_processadas=5,
        bytes_extraidos=1024,
        taxa_erro=0.0,
        tentativa_atual=1,
    )
    db.add(execucao)
    db.commit()
    db.refresh(execucao)
    return execucao


@pytest.fixture
def execucao_concluida_no_db(db):
    """Cria uma execução concluída no banco de dados para testes."""
    processo = Processo(
        nome="Processo Concluído",
        descricao="Processo criado para testes de monitoramento",
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    execucao = Execucao(
        processo_id=processo.id,
        status=ExecucaoStatus.CONCLUIDO,
        paginas_processadas=10,
        bytes_extraidos=2048,
        taxa_erro=0.0,
        tentativa_atual=1,
    )
    db.add(execucao)
    db.commit()
    db.refresh(execucao)
    return execucao


# ==================== Dashboard Principal ====================


class TestDashboardMonitoramento:
    """Testes do dashboard com monitoramento - PRD-016."""

    def test_dashboard_retorna_html(self, client):
        """GET /dashboard deve retornar HTML."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_tem_execucoes_ativas_section(self, client):
        """Dashboard deve ter seção Execuções Ativas."""
        response = client.get("/dashboard")
        html = response.text
        assert "Execuções Ativas" in html

    def test_dashboard_tem_link_ver_todas_execucoes(self, client):
        """Dashboard deve ter link para /execucoes."""
        response = client.get("/dashboard")
        html = response.text
        assert "/execucoes" in html

    def test_dashboard_tem_polling_htmx_execucoes(self, client):
        """Dashboard deve ter configuração HTMX para polling de execuções ativas."""
        response = client.get("/dashboard")
        html = response.text
        assert "execucoes/ativas" in html
        assert "hx-get" in html

    def test_dashboard_stats_cards_polling(self, client):
        """Dashboard stats devem ter atributos HTMX para polling."""
        response = client.get("/dashboard")
        html = response.text
        # Deve ter seção de HTMX polling (presença de hx-trigger)
        assert "hx-trigger" in html


# ==================== Partials de Dashboard ====================


class TestDashboardStatsPartial:
    """Testes do partial de stats do dashboard - PRD-016."""

    def test_stats_partial_retorna_html(self, client):
        """GET /dashboard/stats deve retornar HTML."""
        response = client.get("/dashboard/stats")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_stats_partial_tem_total_execucoes(self, client):
        """Stats partial deve exibir total de execuções."""
        response = client.get("/dashboard/stats")
        html = response.text
        assert "Total de Execuções" in html

    def test_stats_partial_tem_execucoes_ativas(self, client):
        """Stats partial deve exibir execuções ativas."""
        response = client.get("/dashboard/stats")
        html = response.text
        assert "Execuções Ativas" in html

    def test_stats_partial_tem_taxa_sucesso(self, client):
        """Stats partial deve exibir taxa de sucesso."""
        response = client.get("/dashboard/stats")
        html = response.text
        assert "Taxa de Sucesso" in html

    def test_stats_partial_tem_concluidas(self, client):
        """Stats partial deve exibir execuções concluídas."""
        response = client.get("/dashboard/stats")
        html = response.text
        assert "Concluídas" in html


class TestExecucoesAtivasPartial:
    """Testes do partial de execuções ativas - PRD-016."""

    def test_ativas_partial_retorna_html(self, client):
        """GET /execucoes/ativas deve retornar HTML."""
        response = client.get("/execucoes/ativas")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_ativas_partial_sem_execucoes(self, client):
        """Partial deve exibir mensagem quando não há execuções ativas."""
        response = client.get("/execucoes/ativas")
        html = response.text
        assert "Nenhuma execução ativa" in html or "Execução" in html

    def test_ativas_partial_com_execucao_em_execucao(self, client, execucao_no_db):
        """Partial deve exibir execução em andamento."""
        response = client.get("/execucoes/ativas")
        assert response.status_code == 200
        html = response.text
        assert "em_execucao" in html or "Ver detalhes" in html


# ==================== Lista de Execuções ====================


class TestExecucoesListPage:
    """Testes da página de lista de execuções - PRD-016."""

    def test_lista_retorna_html(self, client):
        """GET /execucoes deve retornar HTML."""
        response = client.get("/execucoes")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_lista_tem_titulo(self, client):
        """Página de lista deve ter título 'Execuções'."""
        response = client.get("/execucoes")
        html = response.text
        assert "Execuções" in html

    def test_lista_tem_filtros_status(self, client):
        """Página deve ter filtros por status."""
        response = client.get("/execucoes")
        html = response.text
        assert "em_execucao" in html
        assert "concluido" in html

    def test_lista_sem_execucoes_exibe_mensagem(self, client):
        """Lista vazia deve exibir mensagem informativa."""
        response = client.get("/execucoes")
        html = response.text
        # Deve ter dica para ir a processos ou mensagem vazia
        assert "Processos" in html or "Nenhuma execução" in html

    def test_lista_com_execucao_no_db(self, client, execucao_no_db):
        """Lista deve exibir execução existente."""
        response = client.get("/execucoes")
        assert response.status_code == 200
        html = response.text
        assert "em_execucao" in html

    def test_lista_filtro_status_concluido(self, client, execucao_concluida_no_db):
        """Filtro por concluido deve retornar execuções concluídas."""
        response = client.get("/execucoes?status=concluido")
        assert response.status_code == 200
        html = response.text
        assert "concluido" in html

    def test_lista_paginacao(self, client):
        """Página aceita parâmetro de página."""
        response = client.get("/execucoes?page=1")
        assert response.status_code == 200


# ==================== Detalhe de Execução ====================


class TestExecucaoDetailPage:
    """Testes da página de detalhe de execução - PRD-016."""

    def test_detail_retorna_html(self, client, execucao_no_db):
        """GET /execucoes/{id} deve retornar HTML."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_detail_exibe_status(self, client, execucao_no_db):
        """Detalhe deve exibir status da execução."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        html = response.text
        assert "em_execucao" in html

    def test_detail_exibe_paginas_processadas(self, client, execucao_no_db):
        """Detalhe deve exibir páginas processadas."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        html = response.text
        assert "Páginas Processadas" in html

    def test_detail_tem_link_paginas(self, client, execucao_no_db):
        """Detalhe deve ter link para páginas extraídas."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        html = response.text
        assert "paginas" in html.lower() or "Páginas" in html

    def test_detail_tem_secao_logs(self, client, execucao_no_db):
        """Detalhe deve ter seção de logs."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        html = response.text
        assert "Logs" in html

    def test_detail_tem_sse_script(self, client, execucao_no_db):
        """Detalhe deve ter script SSE para streaming de logs."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        html = response.text
        assert "EventSource" in html or "logs/stream" in html

    def test_detail_execucao_nao_encontrada(self, client):
        """Execução inexistente deve retornar 404."""
        response = client.get(f"/execucoes/{uuid4()}")
        assert response.status_code == 404

    def test_detail_progress_polling(self, client, execucao_no_db):
        """Detalhe deve ter polling para progress bar quando em execução."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        html = response.text
        assert "progress" in html

    def test_detail_botao_cancelar_para_execucao_ativa(self, client, execucao_no_db):
        """Detalhe deve ter botão cancelar para execução ativa."""
        response = client.get(f"/execucoes/{execucao_no_db.id}")
        html = response.text
        assert "Cancelar" in html

    def test_detail_sem_botao_cancelar_para_concluida(
        self, client, execucao_concluida_no_db
    ):
        """Detalhe não deve ter botão cancelar para execução concluída."""
        response = client.get(f"/execucoes/{execucao_concluida_no_db.id}")
        html = response.text
        assert "concluido" in html


# ==================== Progress Bar Partial ====================


class TestProgressBarPartial:
    """Testes do partial de progress bar - PRD-016."""

    def test_progress_retorna_html(self, client, execucao_no_db):
        """GET /execucoes/{id}/progress deve retornar HTML."""
        response = client.get(f"/execucoes/{execucao_no_db.id}/progress")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_progress_exibe_paginas_processadas(self, client, execucao_no_db):
        """Progress partial deve exibir contagem de páginas."""
        response = client.get(f"/execucoes/{execucao_no_db.id}/progress")
        html = response.text
        assert (
            "paginas_processadas" in html
            or str(execucao_no_db.paginas_processadas) in html
        )

    def test_progress_execucao_nao_encontrada(self, client):
        """Progress de execução inexistente deve retornar 404."""
        response = client.get(f"/execucoes/{uuid4()}/progress")
        assert response.status_code == 404
