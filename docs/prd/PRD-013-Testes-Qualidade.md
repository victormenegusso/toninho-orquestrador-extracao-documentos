# PRD-013: Testes e Qualidade

**Status**: ✅ Concluído  
**Prioridade**: 🟡 Média - Backend Features Avançadas (Prioridade 3)  
**Categoria**: Backend - Features Avançadas  
**Estimativa**: 10-12 horas

---

## 1. Objetivo

Estabelecer sistema completo de testes automatizados e controle de qualidade. Inclui configuração de pytest, testes unitários, testes de integração, fixtures, mocks, coverage reporting e CI/CD pipeline básico. Meta: **90% de cobertura**.

## 2. Contexto e Justificativa

Testes são essenciais para:
- **Confiabilidade**: Garantir código funciona como esperado
- **Refactoring**: Mudar código com segurança
- **Documentação**: Testes são documentação viva
- **CI/CD**: Automação de deploy

**Tipos de testes:**
- **Unit**: Testa funções/classes isoladas
- **Integration**: Testa interação entre componentes
- **E2E**: Testa fluxos completos

**Ferramentas:**
- pytest + pytest-asyncio
- pytest-cov para coverage
- pytest-mock para mocks
- httpx-mock para requests HTTP
- testcontainers (opcional) para Redis/DB

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
tests/
├── conftest.py                    # Fixtures globais
├── pytest.ini                     # Configuração pytest
│
├── unit/                          # Testes unitários
│   ├── test_models.py
│   ├── test_schemas.py
│   ├── test_repositories.py
│   ├── test_services.py
│   ├── test_extraction.py
│   └── test_monitoring.py
│
├── integration/                   # Testes de integração
│   ├── test_api_processo.py
│   ├── test_api_execucao.py
│   ├── test_workers.py
│   ├── test_health_checks.py
│   └── test_websocket.py
│
├── e2e/                          # Testes end-to-end (opcional)
│   └── test_full_extraction_flow.py
│
└── fixtures/                     # Fixtures e test data
    ├── sample_pages/
    │   └── example.html
    └── test_data.py
```

### 3.2. Configuração Pytest (pytest.ini)

```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output
addopts =
    -ra
    -v
    --strict-markers
    --strict-config
    --cov=toninho
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=90

# Async
asyncio_mode = auto

# Markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests (> 1s)
    requires_redis: Tests that require Redis
    requires_celery: Tests that require Celery workers

# Ignore
norecursedirs = .git .tox venv env __pycache__ htmlcov .pytest_cache node_modules

# Warnings
filterwarnings =
    error
    ignore::DeprecationWarning
```

### 3.3. Fixtures Globais (tests/conftest.py)

```python
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from toninho.database import Base, get_db
from toninho.main import app
from toninho.config import get_settings

# ============================================================
# DATABASE FIXTURES
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop para testes async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_engine():
    """
    Cria engine de teste (SQLite in-memory)
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Sessão de database para testes
    """
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client para testes de API
    Override dependency get_db
    """
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

# ============================================================
# MODEL FIXTURES
# ============================================================

@pytest.fixture
async def processo_factory(db_session: AsyncSession):
    """Factory para criar Processos de teste"""
    async def _create_processo(**kwargs):
        from toninho.models import Processo
        
        default_data = {
            "nome": "Processo Teste",
            "descricao": "Descrição teste",
            "status": ProcessoStatus.ATIVO
        }
        default_data.update(kwargs)
        
        processo = Processo(**default_data)
        db_session.add(processo)
        await db_session.commit()
        await db_session.refresh(processo)
        
        return processo
    
    return _create_processo

@pytest.fixture
async def configuracao_factory(db_session: AsyncSession):
    """Factory para criar Configurações de teste"""
    async def _create_configuracao(processo_id: UUID, **kwargs):
        from toninho.models import Configuracao
        
        default_data = {
            "processo_id": processo_id,
            "urls": ["https://example.com"],
            "tipo_extracao": TipoExtracao.SIMPLES,
            "timeout": 30
        }
        default_data.update(kwargs)
        
        config = Configuracao(**default_data)
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)
        
        return config
    
    return _create_configuracao

@pytest.fixture
async def execucao_factory(db_session: AsyncSession):
    """Factory para criar Execuções de teste"""
    async def _create_execucao(processo_id: UUID, **kwargs):
        from toninho.models import Execucao
        
        default_data = {
            "processo_id": processo_id,
            "status": ExecucaoStatus.CRIADO,
            "total_urls": 1,
            "urls_processadas": 0
        }
        default_data.update(kwargs)
        
        execucao = Execucao(**default_data)
        db_session.add(execucao)
        await db_session.commit()
        await db_session.refresh(execucao)
        
        return execucao
    
    return _create_execucao

# ============================================================
# MOCK FIXTURES
# ============================================================

@pytest.fixture
def mock_http_client(mocker):
    """Mock HTTPClient para evitar requests reais"""
    mock = mocker.patch("toninho.extraction.http_client.HTTPClient.get")
    
    mock.return_value = {
        "content": b"<html><body><h1>Test Page</h1></body></html>",
        "status_code": 200,
        "headers": {"content-type": "text/html"},
        "from_cache": False
    }
    
    return mock

@pytest.fixture
def mock_celery_task(mocker):
    """Mock Celery tasks para evitar execução real"""
    mock = mocker.patch("toninho.workers.tasks.executar_processo_task.delay")
    mock.return_value.id = "test-task-id-123"
    return mock

@pytest.fixture
def mock_storage(tmp_path):
    """Mock storage usando tmp_path"""
    from toninho.extraction.storage import LocalFileSystemStorage
    return LocalFileSystemStorage(base_dir=str(tmp_path))

# ============================================================
# DATA FIXTURES
# ============================================================

@pytest.fixture
def sample_html() -> str:
    """HTML de exemplo para testes de extração"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Main Heading</h1>
        <p>This is a test paragraph.</p>
        <a href="https://example.com/link">Example Link</a>
    </body>
    </html>
    """

@pytest.fixture
def sample_markdown() -> str:
    """Markdown de exemplo para testes"""
    return """# Main Heading

This is a test paragraph.

[Example Link](https://example.com/link)
"""
```

### 3.4. Exemplo de Testes Unitários (tests/unit/test_services.py)

```python
import pytest
from uuid import uuid4
from toninho.services.processo_service import ProcessoService
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.models.enums import ProcessoStatus

@pytest.mark.unit
class TestProcessoService:
    """Testes para ProcessoService"""
    
    @pytest.fixture
    def processo_repo(self, db_session):
        return ProcessoRepository(db_session)
    
    @pytest.fixture
    def processo_service(self, processo_repo):
        return ProcessoService(processo_repo)
    
    async def test_criar_processo_sucesso(self, processo_service):
        """Deve criar processo com sucesso"""
        data = {
            "nome": "Novo Processo",
            "descricao": "Descrição teste",
            "status": ProcessoStatus.ATIVO
        }
        
        processo = await processo_service.criar(data)
        
        assert processo is not None
        assert processo.nome == "Novo Processo"
        assert processo.status == ProcessoStatus.ATIVO
    
    async def test_criar_processo_nome_duplicado(
        self,
        processo_service,
        processo_factory
    ):
        """Deve lançar erro se nome duplicado"""
        # Criar primeiro processo
        await processo_factory(nome="Duplicado")
        
        # Tentar criar segundo com mesmo nome
        data = {"nome": "Duplicado", "descricao": "Teste"}
        
        with pytest.raises(ValueError, match="Nome já existe"):
            await processo_service.criar(data)
    
    async def test_listar_processos_com_filtros(
        self,
        processo_service,
        processo_factory
    ):
        """Deve listar processos com filtros"""
        # Criar processos
        await processo_factory(nome="Ativo 1", status=ProcessoStatus.ATIVO)
        await processo_factory(nome="Ativo 2", status=ProcessoStatus.ATIVO)
        await processo_factory(nome="Inativo 1", status=ProcessoStatus.INATIVO)
        
        # Filtrar por status ATIVO
        result = await processo_service.listar(
            filters={"status": ProcessoStatus.ATIVO}
        )
        
        assert result["total"] == 2
        assert all(p.status == ProcessoStatus.ATIVO for p in result["items"])
    
    async def test_deletar_processo_com_execucoes(
        self,
        processo_service,
        processo_factory,
        execucao_factory
    ):
        """Deve deletar processo e suas execuções (cascade)"""
        # Criar processo e execução
        processo = await processo_factory()
        await execucao_factory(processo_id=processo.id)
        
        # Deletar processo
        success = await processo_service.deletar(processo.id)
        
        assert success is True
        
        # Verificar que não existe mais
        result = await processo_service.buscar_por_id(processo.id)
        assert result is None
```

### 3.5. Exemplo de Testes de Integração (tests/integration/test_api_processo.py)

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestProcessoAPI:
    """Testes de integração para API de Processo"""
    
    async def test_criar_processo_via_api(self, client: AsyncClient):
        """POST /api/v1/processos cria processo"""
        payload = {
            "nome": "API Test Processo",
            "descricao": "Criado via API",
            "status": "ATIVO"
        }
        
        response = await client.post("/api/v1/processos", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "API Test Processo"
        assert "id" in data
    
    async def test_listar_processos_paginacao(
        self,
        client: AsyncClient,
        processo_factory
    ):
        """GET /api/v1/processos retorna lista paginada"""
        # Criar 15 processos
        for i in range(15):
            await processo_factory(nome=f"Processo {i}")
        
        # Primeira página
        response = await client.get("/api/v1/processos?page=1&size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
        assert data["page"] == 1
        
        # Segunda página
        response = await client.get("/api/v1/processos?page=2&size=10")
        data = response.json()
        assert len(data["items"]) == 5
    
    async def test_atualizar_processo_parcial(
        self,
        client: AsyncClient,
        processo_factory
    ):
        """PATCH /api/v1/processos/{id} atualiza parcialmente"""
        processo = await processo_factory(nome="Original", descricao="Desc")
        
        payload = {"nome": "Atualizado"}
        
        response = await client.patch(
            f"/api/v1/processos/{processo.id}",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Atualizado"
        assert data["descricao"] == "Desc"  # Não mudou
    
    async def test_deletar_processo_404(self, client: AsyncClient):
        """DELETE /api/v1/processos/{id} retorna 404 se não existe"""
        fake_id = uuid4()
        
        response = await client.delete(f"/api/v1/processos/{fake_id}")
        
        assert response.status_code == 404
```

### 3.6. Testes de Workers (tests/integration/test_workers.py)

```python
import pytest
from unittest.mock import AsyncMock
from toninho.workers.orchestrator import ExtractionOrchestrator

@pytest.mark.integration
@pytest.mark.requires_celery
class TestWorkers:
    """Testes para Celery workers"""
    
    async def test_orchestrator_executa_extracao(
        self,
        db_session,
        processo_factory,
        configuracao_factory,
        execucao_factory,
        mock_http_client,
        mock_storage
    ):
        """ExtractionOrchestrator extrai URLs com sucesso"""
        # Setup
        processo = await processo_factory()
        config = await configuracao_factory(
            processo_id=processo.id,
            urls=["https://example.com/page1", "https://example.com/page2"]
        )
        execucao = await execucao_factory(
            processo_id=processo.id,
            total_urls=2
        )
        
        # Run orchestrator
        orchestrator = ExtractionOrchestrator(
            db_session,
            mock_storage
        )
        
        await orchestrator.run(execucao.id)
        
        # Verificar
        await db_session.refresh(execucao)
        
        assert execucao.status == ExecucaoStatus.CONCLUIDO
        assert execucao.urls_processadas == 2
        assert execucao.urls_sucesso == 2
        assert execucao.urls_erro == 0
    
    async def test_orchestrator_trata_erro_de_url(
        self,
        db_session,
        processo_factory,
        configuracao_factory,
        execucao_factory,
        mocker,
        mock_storage
    ):
        """Orchestrator trata erro em URL individual"""
        # Mock HTTP client para lançar erro
        mock_http = mocker.patch("toninho.extraction.http_client.HTTPClient.get")
        mock_http.side_effect = Exception("Network error")
        
        # Setup
        processo = await processo_factory()
        config = await configuracao_factory(
            processo_id=processo.id,
            urls=["https://example.com/page1"]
        )
        execucao = await execucao_factory(
            processo_id=processo.id,
            total_urls=1
        )
        
        # Run
        orchestrator = ExtractionOrchestrator(db_session, mock_storage)
        await orchestrator.run(execucao.id)
        
        # Verificar
        await db_session.refresh(execucao)
        
        assert execucao.status == ExecucaoStatus.CONCLUIDO
        assert execucao.urls_erro == 1
```

### 3.7. Coverage Report

**Script para gerar report:** `scripts/coverage.sh`
```bash
#!/bin/bash
# Gera relatório de coverage

set -e

echo "Running tests with coverage..."

pytest \
    --cov=toninho \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml \
    --cov-fail-under=90

echo ""
echo "Coverage report generated:"
echo "  - Terminal: above"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
```

## 4. Dependências

### 4.1. Bibliotecas (pyproject.toml)
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
httpx = "^0.26.0"
faker = "^21.0.0"  # Para gerar dados de teste
```

### 4.2. Dependências de Outros PRDs
- Todos os PRDs anteriores (001-012)

## 5. Regras de Negócio

### 5.1. Cobertura de Testes
- Meta mínima: **90%**
- Falhar CI se < 90%

### 5.2. Tipos de Testes
- Unit tests: ~70% dos testes
- Integration tests: ~25% dos testes
- E2E tests: ~5% dos testes

### 5.3. Marcadores Pytest
- `@pytest.mark.unit`: Testes unitários
- `@pytest.mark.integration`: Testes de integração
- `@pytest.mark.slow`: Testes lentos
- `@pytest.mark.requires_redis`: Requer Redis
- `@pytest.mark.requires_celery`: Requer Celery

### 5.4. Fixtures
- Usar factories para criar modelos de teste
- Cada teste deve ter database limpa (rollback após teste)
- Mocks para serviços externos (HTTP, Celery)

## 6. Casos de Teste

### 6.1. Coverage por Módulo
- ✅ Models: 95%+ (simples)
- ✅ Schemas: 90%+
- ✅ Repositories: 90%+
- ✅ Services: 90%+ (regras de negócio)
- ✅ API Routes: 85%+
- ✅ Workers: 80%+ (complexo)
- ✅ Extraction: 85%+

### 6.2. Testes Essenciais
- ✅ CRUD de cada entidade
- ✅ Validações de schemas
- ✅ Regras de negócio
- ✅ Casos de erro
- ✅ Casos de borda
- ✅ Concorrência (se aplicável)

## 7. Critérios de Aceitação

### ✅ Configuração
- [ ] pytest configurado
- [ ] pytest-cov configurado
- [ ] Fixtures globais criadas

### ✅ Testes Unitários
- [ ] Testes para models
- [ ] Testes para schemas
- [ ] Testes para repositories
- [ ] Testes para services

### ✅ Testes de Integração
- [ ] Testes para API endpoints
- [ ] Testes para workers
- [ ] Testes para WebSocket

### ✅ Coverage
- [ ] Coverage > 90%
- [ ] Report HTML gerado
- [ ] Report XML para CI

### ✅ CI/CD
- [ ] GitHub Actions configurado (básico)
- [ ] Testes rodando em CI

## 8. Notas de Implementação

### 8.1. Rodando Testes

```bash
# Todos os testes
pytest

# Apenas unit tests
pytest -m unit

# Apenas integration tests
pytest -m integration

# Com coverage
pytest --cov=toninho --cov-report=html

# Específico
pytest tests/unit/test_services.py

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

### 8.2. GitHub Actions CI (Básico)

`.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run tests
        run: poetry run pytest --cov=toninho --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### 8.3. Pre-commit Hooks

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
  
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
  
  - repo: local
    hooks:
      - id: pytest-quick
        name: pytest-quick
        entry: poetry run pytest -m unit
        language: system
        pass_filenames: false
        always_run: true
```

## 9. Referências Técnicas

- **pytest**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **Coverage.py**: https://coverage.readthedocs.io/

## 10. Definição de Pronto

- ✅ pytest configurado com plugins
- ✅ Fixtures globais criadas
- ✅ Testes unitários para todos os módulos
- ✅ Testes de integração para APIs
- ✅ Testes de workers
- ✅ Coverage > 90%
- ✅ CI configurado executando testes
- ✅ Documentação de como rodar testes

---

**PRD Anterior**: PRD-012 - Monitoramento e Métricas  
**Próximo PRD**: PRD-014 - Setup Frontend
