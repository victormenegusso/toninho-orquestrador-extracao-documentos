"""
Testes de integração para Interface CRUD de Processos (PRD-015).

Testa as rotas HTML de processos que servem os templates Jinja2.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from toninho.core.database import get_db
from toninho.main import app
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
def processo_no_db(db):
    """Cria um processo no banco de dados para testes."""
    processo = Processo(
        nome="Processo de Teste",
        descricao="Processo criado para testes de frontend",
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)
    return processo


class TestProcessosListPage:
    """Testes da página de listagem de processos - PRD-015."""

    def test_lista_retorna_html(self, client):
        """GET /processos deve retornar HTML."""
        response = client.get("/processos")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_lista_tem_titulo(self, client):
        """Página de lista deve ter título 'Processos'."""
        response = client.get("/processos")
        html = response.text
        assert "Processos" in html

    def test_lista_tem_botao_novo_processo(self, client):
        """Página deve ter botão para criar novo processo."""
        response = client.get("/processos")
        html = response.text
        assert "Novo Processo" in html
        assert "/processos/novo" in html

    def test_lista_tem_campo_busca(self, client):
        """Página deve ter campo de busca."""
        response = client.get("/processos")
        html = response.text
        assert "Buscar" in html
        assert "processos/search" in html

    def test_lista_tem_filtro_status(self, client):
        """Página deve ter filtro por status."""
        response = client.get("/processos")
        html = response.text
        assert "Status" in html
        assert "Ativo" in html
        assert "Inativo" in html

    def test_lista_vazia_mostra_estado_vazio(self, client):
        """Com BD vazio, deve mostrar mensagem de nenhum processo."""
        response = client.get("/processos")
        html = response.text
        assert "Nenhum processo" in html

    def test_lista_com_processo_mostra_processo(self, client, processo_no_db):
        """Com processo no BD, deve exibi-lo na tabela."""
        response = client.get("/processos")
        html = response.text
        assert "Processo de Teste" in html

    def test_lista_com_paginacao(self, client):
        """Lista deve funcionar com parâmetro de paginação."""
        response = client.get("/processos?page=1")
        assert response.status_code == 200

    def test_lista_com_filtro_status_ativo(self, client):
        """Lista deve aceitar filtro por status ATIVO."""
        response = client.get("/processos?status=ATIVO")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_lista_com_filtro_status_inativo(self, client):
        """Lista deve aceitar filtro por status INATIVO."""
        response = client.get("/processos?status=INATIVO")
        assert response.status_code == 200

    def test_lista_com_busca(self, client, processo_no_db):
        """Lista deve funcionar com parâmetro de busca."""
        response = client.get("/processos?search=Processo")
        assert response.status_code == 200
        html = response.text
        assert "Processo de Teste" in html

    def test_lista_tem_sidebar(self, client):
        """Lista deve ter sidebar de navegação."""
        response = client.get("/processos")
        html = response.text
        assert "Dashboard" in html


class TestProcessosSearchPartial:
    """Testes do partial HTMX de busca de processos."""

    def test_search_retorna_html(self, client):
        """GET /processos/search deve retornar HTML parcial."""
        response = client.get("/processos/search")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_search_sem_resultados(self, client):
        """Busca sem resultados deve mostrar estado vazio."""
        response = client.get("/processos/search?search=xxxxxxxxxx_nao_existe")
        assert response.status_code == 200
        html = response.text
        assert "Nenhum processo" in html

    def test_search_com_resultados(self, client, processo_no_db):
        """Busca com correspondência deve retornar o processo."""
        response = client.get("/processos/search?search=Teste")
        assert response.status_code == 200
        html = response.text
        assert "Processo de Teste" in html

    def test_search_com_filtro_status(self, client, processo_no_db):
        """Busca pode ser filtrada por status."""
        response = client.get("/processos/search?status=ATIVO")
        assert response.status_code == 200

    def test_search_partial_nao_tem_sidebar(self, client):
        """Partial de busca não deve incluir sidebar completo."""
        response = client.get("/processos/search")
        html = response.text
        # O partial é só a tabela, não deve ter o layout completo
        assert "<html" not in html.lower()

    def test_search_partial_tem_tabela(self, client, processo_no_db):
        """Partial deve retornar estrutura de tabela ou estado vazio."""
        response = client.get("/processos/search?search=Teste")
        html = response.text
        assert "table" in html.lower() or "Nenhum processo" in html


class TestProcessosCreatePage:
    """Testes da página de criação de processo."""

    def test_create_retorna_html(self, client):
        """GET /processos/novo deve retornar HTML."""
        response = client.get("/processos/novo")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_create_tem_titulo(self, client):
        """Página de criação deve ter título 'Novo Processo'."""
        response = client.get("/processos/novo")
        html = response.text
        assert "Novo Processo" in html

    def test_create_tem_campo_nome(self, client):
        """Formulário deve ter campo de nome."""
        response = client.get("/processos/novo")
        html = response.text
        assert 'name="nome"' in html

    def test_create_tem_campo_descricao(self, client):
        """Formulário deve ter campo de descrição."""
        response = client.get("/processos/novo")
        html = response.text
        assert 'name="descricao"' in html

    def test_create_tem_campo_status(self, client):
        """Formulário deve ter campo de status."""
        response = client.get("/processos/novo")
        html = response.text
        assert 'name="status"' in html

    def test_create_tem_botao_submit(self, client):
        """Formulário deve ter botão de submit."""
        response = client.get("/processos/novo")
        html = response.text
        assert "Criar Processo" in html

    def test_create_tem_link_cancelar(self, client):
        """Formulário deve ter link para cancelar."""
        response = client.get("/processos/novo")
        html = response.text
        assert "Cancelar" in html
        assert "/processos" in html

    def test_create_target_api(self, client):
        """Formulário deve apontar para a API de processos."""
        response = client.get("/processos/novo")
        html = response.text
        assert "/api/v1/processos" in html


class TestProcessosEditPage:
    """Testes da página de edição de processo."""

    def test_edit_retorna_html(self, client, processo_no_db):
        """GET /processos/{id}/editar deve retornar HTML."""
        response = client.get(f"/processos/{processo_no_db.id}/editar")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_edit_mostra_nome_do_processo(self, client, processo_no_db):
        """Página de edição deve mostrar os dados do processo."""
        response = client.get(f"/processos/{processo_no_db.id}/editar")
        html = response.text
        assert "Processo de Teste" in html

    def test_edit_tem_botao_salvar(self, client, processo_no_db):
        """Formulário de edição deve ter botão de salvar."""
        response = client.get(f"/processos/{processo_no_db.id}/editar")
        html = response.text
        assert "Salvar Alterações" in html

    def test_edit_titulo_indica_edicao(self, client, processo_no_db):
        """Formulário de edição deve indicar que está editando."""
        response = client.get(f"/processos/{processo_no_db.id}/editar")
        html = response.text
        assert "Editar" in html

    def test_edit_id_inexistente_retorna_404(self, client):
        """Editar processo inexistente deve retornar 404."""
        response = client.get(f"/processos/{uuid4()}/editar")
        assert response.status_code == 404

    def test_edit_form_aponta_para_api(self, client, processo_no_db):
        """Formulário de edição deve apontar para a API do processo."""
        response = client.get(f"/processos/{processo_no_db.id}/editar")
        html = response.text
        assert str(processo_no_db.id) in html


class TestProcessosDetailPage:
    """Testes da página de detalhes de processo."""

    def test_detail_retorna_html(self, client, processo_no_db):
        """GET /processos/{id} deve retornar HTML."""
        response = client.get(f"/processos/{processo_no_db.id}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_detail_mostra_nome(self, client, processo_no_db):
        """Página de detalhes deve mostrar o nome do processo."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert "Processo de Teste" in html

    def test_detail_mostra_descricao(self, client, processo_no_db):
        """Página de detalhes deve mostrar a descrição."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert "Processo criado para testes de frontend" in html

    def test_detail_tem_botao_editar(self, client, processo_no_db):
        """Página de detalhes deve ter botão para editar."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert "Editar" in html
        assert f"/processos/{processo_no_db.id}/editar" in html

    def test_detail_tem_botao_executar(self, client, processo_no_db):
        """Página de detalhes deve ter botão para executar."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert "Executar" in html

    def test_detail_tem_stats(self, client, processo_no_db):
        """Página de detalhes deve mostrar estatísticas."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert "Total de Execuções" in html

    def test_detail_tem_secao_execucoes(self, client, processo_no_db):
        """Página de detalhes deve ter seção de execuções recentes."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert "Execuções Recentes" in html

    def test_detail_tem_link_voltar(self, client, processo_no_db):
        """Página de detalhes deve ter link para voltar à lista."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert "/processos" in html

    def test_detail_id_inexistente_retorna_404(self, client):
        """Detalhe de processo inexistente deve retornar 404."""
        response = client.get(f"/processos/{uuid4()}")
        assert response.status_code == 404

    def test_detail_mostra_id_do_processo(self, client, processo_no_db):
        """Página de detalhes deve mostrar o ID do processo."""
        response = client.get(f"/processos/{processo_no_db.id}")
        html = response.text
        assert str(processo_no_db.id) in html
