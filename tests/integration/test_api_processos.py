"""Testes de integração para API de Processos."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from toninho.core.database import get_db
from toninho.main import app
from toninho.models.enums import ExecucaoStatus, ProcessoStatus
from toninho.models.execucao import Execucao
from toninho.models.processo import Processo


@pytest.fixture
def client(db):
    """Fixture que retorna cliente de teste com override de database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()



class TestProcessosAPI:
    """Testes de integração da API de Processos."""

    def test_create_processo_sucesso(self, client, db):
        """Testa criação de processo via API."""
        payload = {
            "nome": "Processo API Teste",
            "descricao": "Descrição via API",
            "status": "ATIVO",
        }
        
        response = client.post("/api/v1/processos", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["nome"] == payload["nome"]
        assert data["data"]["descricao"] == payload["descricao"]
        assert "id" in data["data"]

    def test_create_processo_nome_duplicado(self, client, db, processo_factory):
        """Testa criação com nome duplicado."""
        # Criar processo existente
        processo = processo_factory(nome="Processo Duplicado")
        
        # Tentar criar com mesmo nome
        payload = {
            "nome": "Processo Duplicado",
            "descricao": "Teste",
        }
        
        response = client.post("/api/v1/processos", json=payload)
        
        assert response.status_code == 409

    def test_create_processo_dados_invalidos(self, client):
        """Testa criação com dados inválidos."""
        payload = {
            "nome": "",  # Nome vazio
            "descricao": "Teste",
        }
        
        response = client.post("/api/v1/processos", json=payload)
        
        assert response.status_code == 422

    def test_list_processos_vazio(self, client, db):
        """Testa listagem quando não há processos."""
        response = client.get("/api/v1/processos")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_processos_com_dados(self, client, db, processo_factory):
        """Testa listagem com processos."""
        # Criar processos
        for i in range(5):
            processo_factory(nome=f"Processo {i}")
        
        response = client.get("/api/v1/processos")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["page"] == 1

    def test_list_processos_paginacao(self, client, db, processo_factory):
        """Testa paginação da listagem."""
        # Criar 10 processos
        for i in range(10):
            processo_factory(nome=f"Processo {i}")
        
        # Primeira página
        response = client.get("/api/v1/processos?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["total"] == 10
        assert data["pagination"]["total_pages"] == 2
        
        # Segunda página
        response = client.get("/api/v1/processos?page=2&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["page"] == 2

    def test_list_processos_filtro_status(self, client, db, processo_factory):
        """Testa filtro por status."""
        # Criar processos com status diferentes
        processo_factory(nome="Ativo 1", status=ProcessoStatus.ATIVO)
        processo_factory(nome="Ativo 2", status=ProcessoStatus.ATIVO)
        processo_factory(nome="Inativo 1", status=ProcessoStatus.INATIVO)
        
        # Filtrar por ATIVO
        response = client.get("/api/v1/processos?status=ATIVO")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2

    def test_list_processos_busca(self, client, db, processo_factory):
        """Testa busca por nome."""
        processo_factory(nome="Processo ABC")
        processo_factory(nome="Processo XYZ")
        processo_factory(nome="Outro Nome")
        
        response = client.get("/api/v1/processos?busca=Processo")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

    def test_get_processo_existente(self, client, db, processo_factory):
        """Testa busca de processo por ID."""
        processo = processo_factory(nome="Processo Teste")
        
        response = client.get(f"/api/v1/processos/{processo.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(processo.id)
        assert data["data"]["nome"] == "Processo Teste"

    def test_get_processo_nao_encontrado(self, client):
        """Testa busca de processo inexistente."""
        fake_id = uuid4()
        
        response = client.get(f"/api/v1/processos/{fake_id}")
        
        assert response.status_code == 404

    def test_get_processo_detail(self, client, db, processo_factory):
        """Testa busca de detalhes completos."""
        processo = processo_factory(nome="Processo Detalhado")
        
        response = client.get(f"/api/v1/processos/{processo.id}/detalhes")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(processo.id)
        assert "configuracoes" in data["data"]
        assert "execucoes_recentes" in data["data"]
        assert "total_execucoes" in data["data"]

    def test_update_processo_sucesso(self, client, db, processo_factory):
        """Testa atualização de processo."""
        processo = processo_factory(nome="Nome Original")
        
        payload = {
            "nome": "Nome Atualizado",
            "descricao": "Descrição atualizada",
            "status": "INATIVO",
        }
        
        response = client.put(f"/api/v1/processos/{processo.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["nome"] == "Nome Atualizado"
        assert data["data"]["status"] == "INATIVO"

    def test_update_processo_nao_encontrado(self, client):
        """Testa atualização de processo inexistente."""
        fake_id = uuid4()
        payload = {"nome": "Novo Nome"}
        
        response = client.put(f"/api/v1/processos/{fake_id}", json=payload)
        
        assert response.status_code == 404

    def test_update_processo_nome_duplicado(self, client, db, processo_factory):
        """Testa atualização com nome já existente."""
        processo1 = processo_factory(nome="Processo 1")
        processo2 = processo_factory(nome="Processo 2")
        
        # Tentar renomear processo1 para "Processo 2"
        payload = {"nome": "Processo 2"}
        
        response = client.put(f"/api/v1/processos/{processo1.id}", json=payload)
        
        assert response.status_code == 409

    def test_patch_processo_sucesso(self, client, db, processo_factory):
        """Testa atualização parcial."""
        processo = processo_factory(
            nome="Nome Original", descricao="Descrição original"
        )
        
        # Atualizar apenas nome
        payload = {"nome": "Nome Atualizado"}
        
        response = client.patch(f"/api/v1/processos/{processo.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["nome"] == "Nome Atualizado"
        # Descrição deve permanecer
        assert data["data"]["descricao"] == "Descrição original"

    def test_delete_processo_sucesso(self, client, db, processo_factory):
        """Testa deleção de processo."""
        processo = processo_factory(nome="Processo para Deletar")
        processo_id = processo.id
        
        response = client.delete(f"/api/v1/processos/{processo_id}")
        
        assert response.status_code == 204
        
        # Verificar que foi deletado
        response = client.get(f"/api/v1/processos/{processo_id}")
        assert response.status_code == 404

    def test_delete_processo_nao_encontrado(self, client):
        """Testa deleção de processo inexistente."""
        fake_id = uuid4()
        
        response = client.delete(f"/api/v1/processos/{fake_id}")
        
        assert response.status_code == 404

    def test_delete_processo_com_execucao_em_andamento(
        self, client, db, processo_factory, execucao_factory
    ):
        """Testa deleção com execução em andamento."""
        processo = processo_factory(nome="Processo com Execução")
        
        # Criar execução em andamento
        execucao_factory(
            processo_id=processo.id, status=ExecucaoStatus.EM_EXECUCAO
        )
        
        response = client.delete(f"/api/v1/processos/{processo.id}")
        
        assert response.status_code == 409

    def test_get_processo_metricas(self, client, db, processo_factory):
        """Testa endpoint de métricas."""
        processo = processo_factory(nome="Processo Metricas")
        
        response = client.get(f"/api/v1/processos/{processo.id}/metricas")
        
        assert response.status_code == 200
        data = response.json()
        assert "processo_id" in data["data"]
        assert "total_execucoes" in data["data"]
        assert "execucoes_sucesso" in data["data"]
        assert "taxa_sucesso" in data["data"]

    def test_get_metricas_processo_nao_encontrado(self, client):
        """Testa métricas de processo inexistente."""
        fake_id = uuid4()
        
        response = client.get(f"/api/v1/processos/{fake_id}/metricas")
        
        assert response.status_code == 404

    def test_list_processos_ordenacao(self, client, db, processo_factory):
        """Testa ordenação da listagem."""
        # Criar processos
        processo_factory(nome="B Processo")
        processo_factory(nome="A Processo")
        processo_factory(nome="C Processo")
        
        # Ordenar por nome ASC
        response = client.get("/api/v1/processos?order_by=nome&order_dir=asc")
        assert response.status_code == 200
        data = response.json()
        assert data["data"][0]["nome"] == "A Processo"
        assert data["data"][1]["nome"] == "B Processo"
        assert data["data"][2]["nome"] == "C Processo"
        
        # Ordenar por nome DESC
        response = client.get("/api/v1/processos?order_by=nome&order_dir=desc")
        assert response.status_code == 200
        data = response.json()
        assert data["data"][0]["nome"] == "C Processo"

    def test_list_processos_parametros_invalidos(self, client):
        """Testa validação de parâmetros."""
        # Page = 0
        response = client.get("/api/v1/processos?page=0")
        assert response.status_code == 400
        
        # Per_page > 100
        response = client.get("/api/v1/processos?per_page=101")
        assert response.status_code == 400

    def test_workflow_completo(self, client, db):
        """Testa workflow completo de CRUD."""
        # 1. Criar processo
        create_payload = {
            "nome": "Processo Workflow",
            "descricao": "Teste workflow completo",
            "status": "ATIVO",
        }
        response = client.post("/api/v1/processos", json=create_payload)
        assert response.status_code == 201
        processo_id = response.json()["data"]["id"]
        
        # 2. Listar e verificar
        response = client.get("/api/v1/processos")
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 1
        
        # 3. Obter detalhes
        response = client.get(f"/api/v1/processos/{processo_id}")
        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Processo Workflow"
        
        # 4. Atualizar
        update_payload = {"nome": "Processo Workflow Atualizado"}
        response = client.patch(f"/api/v1/processos/{processo_id}", json=update_payload)
        assert response.status_code == 200
        assert response.json()["data"]["nome"] == "Processo Workflow Atualizado"
        
        # 5. Obter métricas
        response = client.get(f"/api/v1/processos/{processo_id}/metricas")
        assert response.status_code == 200
        
        # 6. Deletar
        response = client.delete(f"/api/v1/processos/{processo_id}")
        assert response.status_code == 204
        
        # 7. Verificar que foi deletado
        response = client.get(f"/api/v1/processos/{processo_id}")
        assert response.status_code == 404
