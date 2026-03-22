# 🧪 Guia de Testes — Toninho Processo Extração

## 1. Visão Geral

O projeto utiliza **pytest** como framework de testes com as seguintes configurações principais:

- **Cobertura mínima:** 90% (falha o build se não atingir)
- **Modo asyncio:** `auto` (via `pytest-asyncio`) — não é necessário decorar testes async com `@pytest.mark.asyncio`
- **Relatórios de cobertura:** HTML (`htmlcov/`), terminal com linhas faltantes e XML (`coverage.xml`)
- **Filtros de warning:** `DeprecationWarning` e `PytestUnraisableExceptionWarning` são ignorados

Configuração completa em `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=toninho --cov-report=html --cov-report=term-missing --cov-report=xml --cov-fail-under=90"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests (> 1s)",
    "requires_redis: Tests that require Redis",
    "requires_celery: Tests that require Celery workers"
]
```

---

## 2. Estrutura de Testes

```
tests/
├── conftest.py                          # Fixtures globais (db, factories, mocks)
├── unit/                                # Testes unitários
│   ├── test_config.py
│   ├── test_configuracao_repository.py
│   ├── test_configuracao_service.py
│   ├── test_constants.py
│   ├── test_exceptions.py
│   ├── test_execucao_repository.py
│   ├── test_execucao_service.py
│   ├── test_integration_models_schemas.py
│   ├── test_log_repository.py
│   ├── test_log_service.py
│   ├── test_models.py
│   ├── test_pagina_extraida_repository.py
│   ├── test_pagina_extraida_service.py
│   ├── test_processo_repository.py
│   ├── test_processo_service.py
│   ├── test_schemas.py
│   ├── extraction/                      # Módulo de extração
│   │   ├── test_browser_client.py
│   │   ├── test_docling_extractor.py
│   │   ├── test_extractor.py
│   │   ├── test_http_client.py
│   │   ├── test_markdown_converter.py
│   │   ├── test_storage.py
│   │   └── test_utils.py
│   ├── monitoring/                      # Módulo de monitoramento
│   │   ├── test_health.py
│   │   ├── test_metrics.py
│   │   ├── test_routes.py
│   │   └── test_websocket.py
│   └── workers/                         # Workers Celery
│       ├── test_celery_app.py
│       ├── test_orchestrator.py
│       └── test_tasks.py
├── integration/                         # Testes de integração (API + Frontend)
│   ├── test_api.py
│   ├── test_api_configuracoes.py
│   ├── test_api_execucoes.py
│   ├── test_api_logs.py
│   ├── test_api_paginas_extraidas.py
│   ├── test_api_processos.py
│   ├── test_frontend.py
│   ├── test_frontend_downloads.py
│   ├── test_frontend_monitoring.py
│   ├── test_frontend_processos.py
│   └── test_workers_docling.py
└── e2e/                                 # Testes end-to-end (Playwright)
    ├── conftest.py                      # Fixtures E2E (live server, API client)
    ├── test_smoke.py
    ├── test_uc01_criar_processo.py
    ├── test_uc02_validacao_formulario.py
    ├── test_uc03_editar_processo.py
    ├── test_uc04_busca_processos.py
    ├── test_uc05_executar_processo.py
    ├── test_uc06_deletar_processo.py
    ├── test_uc07_dashboard_polling.py
    ├── test_uc08_logs_sse.py
    ├── test_uc09_ciclo_vida_execucao.py
    ├── test_uc10_listagem_execucoes.py
    ├── test_uc11_paginas_extraidas.py
    ├── test_uc12_notificacoes.py
    ├── test_uc13_navegacao.py
    └── test_uc14_erros_rede.py
```

---

## 3. Como Rodar

| Comando | Descrição |
|---------|-----------|
| `make test` | Roda testes unitários + integração com cobertura (mínimo 90%) |
| `make test-e2e` | Roda testes E2E com Playwright em modo headless |
| `make test-e2e-headed` | Roda testes E2E com browser visível |
| `make test-e2e-debug TEST=<path>` | Roda um único teste E2E em modo debug |
| `make quality` | Pipeline completo: check + lint + security + audit + test |

### Exemplos de uso

```bash
# Rodar todos os testes (unit + integration)
make test

# Rodar apenas testes unitários
pytest tests/unit/ -v

# Rodar apenas testes de integração
pytest tests/integration/ -v

# Rodar E2E headless
make test-e2e

# Rodar E2E com browser visível (útil para debug)
make test-e2e-headed

# Debugar um teste E2E específico
make test-e2e-debug TEST=tests/e2e/test_uc01_criar_processo.py

# Rodar testes por marker
pytest -m unit
pytest -m integration
pytest -m "not slow"
pytest -m "not requires_redis"

# Rodar testes com output verbose
pytest tests/unit/ -v --tb=short
```

---

## 4. Pré-requisitos para E2E

### Instalação do Playwright

```bash
# Instalar browsers do Playwright
playwright install chromium

# Ou instalar todos os browsers
playwright install
```

### Serviços necessários

Os testes E2E **não** dependem de Redis ou Celery. O `conftest.py` do E2E:

1. Cria um banco SQLite temporário
2. Roda as migrations do Alembic
3. Sobe um servidor FastAPI/Uvicorn na porta **8089**
4. Aguarda o health check responder (timeout de 30s)
5. Limpa tudo ao final da sessão

> ⚠️ **Porta 8089:** Certifique-se de que a porta não está em uso antes de rodar os testes E2E.

---

## 5. Mapeamento de Cobertura E2E

**Total: 58 cenários de teste em 15 arquivos**

| Arquivo | UC | Descrição | Cenários |
|---------|-----|-----------|----------|
| `test_smoke.py` | — | Health check básico, carregamento de página, HTMX, Alpine.js, arquivos estáticos | 7 |
| `test_uc01_criar_processo.py` | UC-01 | Criação de processo com formulário Alpine.js (config completa, agendamento recorrente, one_time, alerta docling, use_browser) | 5 |
| `test_uc02_validacao_formulario.py` | UC-02 | Validação de formulário (nome vazio, URLs vazias, timeout fora do range, cron inválido, nome duplicado) | 5 |
| `test_uc03_editar_processo.py` | UC-03 | Edição de processo com valores pré-carregados | 1 |
| `test_uc04_busca_processos.py` | UC-04 | Busca e filtros de processos (debounce, filtro status, combinados, sem resultados, limpar) | 5 |
| `test_uc05_executar_processo.py` | UC-05 | Execução de processo (confirmação, cancelar confirmação, executar da página detalhe) | 3 |
| `test_uc06_deletar_processo.py` | UC-06 | Deleção de processo com verificação de persistência | 1 |
| `test_uc07_dashboard_polling.py` | UC-07 | Dashboard com polling HTMX (cards, valores numéricos, polling 3s, stats endpoint, quick actions) | 5 |
| `test_uc08_logs_sse.py` | UC-08 | Logs com SSE streaming (container, logs via SSE, filtro, progress polling 2s, encerramento) | 5 |
| `test_uc09_ciclo_vida_execucao.py` | UC-09 | Ciclo de vida da execução (botões visíveis, pausar, retomar, cancelar) | 4 |
| `test_uc10_listagem_execucoes.py` | UC-10 | Listagem de execuções (colunas, badges status, filtro URL, link detalhes) | 4 |
| `test_uc11_paginas_extraidas.py` | UC-11 | Páginas extraídas (grid cards, busca debounce, filtro combinado, preview modal, download) | 5 |
| `test_uc12_notificacoes.py` | UC-12 | Notificações (alert flash Alpine, htmx response error) | 2 |
| `test_uc13_navegacao.py` | UC-13 | Navegação (sidebar links, rotas, hx-request) | 3 |
| `test_uc14_erros_rede.py` | UC-14 | Erros de rede (erro 500, htmx response error, recuperação polling) | 3 |

---

## 6. Markers do pytest

| Marker | Descrição | Uso |
|--------|-----------|-----|
| `@pytest.mark.unit` | Testes unitários | `pytest -m unit` |
| `@pytest.mark.integration` | Testes de integração | `pytest -m integration` |
| `@pytest.mark.e2e` | Testes end-to-end | `pytest -m e2e` |
| `@pytest.mark.slow` | Testes lentos (> 1s) | `pytest -m "not slow"` |
| `@pytest.mark.requires_redis` | Testes que precisam de Redis | `pytest -m "not requires_redis"` |
| `@pytest.mark.requires_celery` | Testes que precisam de Celery workers | `pytest -m "not requires_celery"` |

### Combinando markers

```bash
# Rodar unit excluindo lentos
pytest -m "unit and not slow"

# Rodar tudo exceto testes que precisam de infraestrutura
pytest -m "not requires_redis and not requires_celery"
```

---

## 7. Fixtures Principais

### 7.1 Fixtures Globais (`tests/conftest.py`)

| Fixture | Escopo | Descrição |
|---------|--------|-----------|
| `test_engine` | function | Engine SQLAlchemy com SQLite temporário (file-based para suportar múltiplas conexões do TestClient) |
| `db` | function | Sessão SQLAlchemy com rollback automático ao final |
| `processo_factory` | function | Factory que cria instâncias de `Processo` com nomes auto-incrementais |
| `execucao_factory` | function | Factory que cria instâncias de `Execucao`, linkando automaticamente a um `Processo` |
| `sample_html` | function | HTML de exemplo em bytes para testes de extração |
| `sample_html_file` | function | Caminho para `tests/fixtures/sample_pages/example.html` |
| `sample_markdown` | function | Conteúdo markdown de exemplo |
| `mock_storage` | function | `LocalFileSystemStorage` apontando para diretório temporário |
| `mock_celery_task` | function | Mock de execução Celery para evitar execução real de tasks |

### 7.2 Fixtures E2E (`tests/e2e/conftest.py`)

| Fixture | Escopo | Descrição |
|---------|--------|-----------|
| `_e2e_db_path` | session | Caminho para SQLite temporário da sessão E2E |
| `_e2e_env` | session | Variáveis de ambiente (DATABASE_URL, DEBUG=false, LOG_LEVEL=WARNING, SQL_ECHO=false) |
| `_run_migrations` | session | Executa `alembic upgrade head` no banco E2E |
| `live_server` | session | Servidor FastAPI/Uvicorn em `127.0.0.1:8089` com health check (timeout 30s) |
| `base_url` | session | URL do servidor live (`http://127.0.0.1:8089`); reconhecida pelo pytest-playwright |
| `api_client` | session | `httpx.Client` conectado ao live server para seeding via API |
| `create_processo` | function | Cria processo via `POST /api/v1/processos` com nome único (UUID suffix) |
| `create_processo_com_config` | function | Cria processo + configuração padrão; retorna tupla `(processo, config)` |
| `create_execucao` | function | Cria execução via API; cria processo automaticamente se `processo_id` não fornecido |
| `update_execucao_status` | function | Atualiza status da execução via `PATCH /api/v1/execucoes/{id}/status` |
| `create_logs_batch` | function | Cria registros de log em lote via `POST /api/v1/logs/batch` |
| `create_paginas_extraidas` | function | Cria execução completa com `paginas_extraidas` e arquivos markdown temporários |

---

## 8. Como Adicionar Novos Testes

### 8.1 Teste Unitário

1. Crie o arquivo em `tests/unit/` seguindo o padrão `test_<módulo>.py`
2. Use as fixtures `db`, `processo_factory`, etc. do `conftest.py` global
3. Marque com `@pytest.mark.unit` (opcional, mas recomendado)

```python
import pytest
from toninho.services.processo_service import ProcessoService

@pytest.mark.unit
class TestProcessoService:
    async def test_criar_processo_com_nome_valido(self, db):
        service = ProcessoService(db)
        processo = await service.criar(nome="Meu Processo", urls=["https://example.com"])
        assert processo.nome == "Meu Processo"
```

### 8.2 Teste de Integração

1. Crie em `tests/integration/` seguindo `test_api_<recurso>.py` ou `test_frontend_<página>.py`
2. Use `TestClient` do FastAPI para testar endpoints
3. Marque com `@pytest.mark.integration`

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
class TestApiProcessos:
    def test_listar_processos_retorna_200(self, client: TestClient):
        response = client.get("/api/v1/processos")
        assert response.status_code == 200
```

### 8.3 Teste E2E

1. Crie em `tests/e2e/` seguindo o padrão `test_uc<XX>_<descrição>.py`
2. Use as fixtures do `tests/e2e/conftest.py` para seeding de dados
3. Use `page` (fixture do pytest-playwright) para interações no browser
4. Marque com `@pytest.mark.e2e`

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
class TestUC15MinhaFeature:
    def test_pagina_carrega_corretamente(self, page: Page, create_processo):
        processo = create_processo(nome="Teste E2E")
        page.goto(f"/processos/{processo['id']}")
        expect(page.locator("h1")).to_contain_text("Teste E2E")

    def test_botao_acao_funciona(self, page: Page, create_processo):
        processo = create_processo()
        page.goto(f"/processos/{processo['id']}")
        page.click("[data-testid='btn-acao']")
        expect(page.locator(".success-message")).to_be_visible()
```

### Convenções

- **Nomeação:** `test_<ação>_<resultado_esperado>` (ex: `test_busca_por_nome_retorna_resultados`)
- **Classes:** `TestUC<XX><Descrição>` para E2E, `Test<Módulo>` para unit/integration
- **Fixtures de seeding:** Sempre use as fixtures do conftest em vez de inserir dados diretamente no banco
- **Assertions E2E:** Prefira `expect()` do Playwright sobre `assert` para melhor output de erro

---

## 9. Gaps de Cobertura Identificados

### Análise: Páginas do Frontend vs. Testes E2E

| Página/Template | Coberta por E2E? | Observação |
|-----------------|:-----------------:|------------|
| `pages/home.html` | ✅ | `test_smoke.py` |
| `pages/dashboard/index.html` | ✅ | `test_smoke.py`, `test_uc07_dashboard_polling.py` |
| `pages/processos/list.html` | ✅ | `test_uc04_busca_processos.py`, `test_uc06_deletar_processo.py` |
| `pages/processos/create.html` | ✅ | `test_uc01_criar_processo.py`, `test_uc02_validacao_formulario.py` |
| `pages/processos/detail.html` | ⚠️ Parcial | `test_uc05_executar_processo.py` cobre execução, mas falta cobertura de visualização geral |
| `pages/execucoes/list.html` | ✅ | `test_uc10_listagem_execucoes.py` |
| `pages/execucoes/detail.html` | ✅ | `test_uc08_logs_sse.py`, `test_uc09_ciclo_vida_execucao.py` |
| `pages/execucoes/paginas.html` | ✅ | `test_uc11_paginas_extraidas.py` |
| `pages/paginas/detail.html` | ❌ | Sem teste E2E dedicado para visualização de detalhe de página extraída |
| `components/sidebar.html` | ✅ | `test_uc13_navegacao.py` |
| `components/modal.html` | ⚠️ Parcial | Testado indiretamente em confirmações de execução/deleção |
| `components/alert.html` | ✅ | `test_uc12_notificacoes.py` |
| `components/preview_modal.html` | ✅ | `test_uc11_paginas_extraidas.py` |
| `components/pagination.html` | ❌ | Sem teste E2E para paginação |
| `components/navbar.html` | ❌ | Sem teste E2E dedicado para navbar |
| `partials/processos_table.html` | ✅ | `test_uc04_busca_processos.py` |
| `partials/paginas_grid.html` | ✅ | `test_uc11_paginas_extraidas.py` |
| `partials/dashboard_stats.html` | ✅ | `test_uc07_dashboard_polling.py` |
| `partials/progress_bar.html` | ⚠️ Parcial | Testado indiretamente via `test_uc08_logs_sse.py` (progress polling) |
| `partials/execucoes_ativas.html` | ✅ | `test_uc07_dashboard_polling.py` |

### Gaps prioritários

1. **`pages/paginas/detail.html`** — Página de detalhe de página extraída sem cobertura E2E. Sugestão: criar `test_uc15_detalhe_pagina.py`
2. **`components/pagination.html`** — Componente de paginação sem teste. Importante testar navegação entre páginas em listagens grandes
3. **`test_uc03_editar_processo.py`** — Apenas 1 cenário. Considerar adicionar: edição parcial, validação na edição, cancelamento de edição
4. **`test_uc06_deletar_processo.py`** — Apenas 1 cenário. Considerar adicionar: cancelar deleção, deletar processo com execuções
5. **`test_uc12_notificacoes.py`** — Apenas 2 cenários. Considerar adicionar: diferentes tipos de notificação, timeout de notificação
6. **Responsividade/Mobile** — Nenhum teste E2E valida comportamento em viewports mobile
7. **Acessibilidade** — Nenhum teste E2E valida atributos ARIA ou navegação por teclado
