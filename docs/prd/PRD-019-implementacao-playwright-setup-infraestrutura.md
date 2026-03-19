# PRD-019: Implementação Playwright — Setup de Infraestrutura E2E

**Status**: 📋 Planejado
**Prioridade**: 🔴 Alta — Pré-requisito para todos os testes E2E
**Categoria**: DevOps + Testing — Infraestrutura
**Estimativa**: 3-4 horas

---

## 1. Objetivo

Configurar toda a infraestrutura necessária para executar testes E2E com Playwright no projeto Toninho. Este PRD **não implementa nenhum caso de uso** — ele cria a base (`conftest.py`, dependências, Makefile targets, configuração pytest) sobre a qual todos os PRDs seguintes (020–025) serão construídos.

> **Importante:** O Playwright deve funcionar em dois modos:
> - **Headless** (padrão) — para CI/CD e execuções automatizadas.
> - **Headed** (visível) — para desenvolvimento, debugging e gravação de testes com `codegen`.

---

## 2. Contexto e Justificativa

### 2.1. Gap Atual

O backend possui cobertura de 90%+ com pytest (unit + integration). O frontend (HTMX + Alpine.js + Jinja2) não possui testes automatizados. Alterações em templates, atributos `hx-*` ou estado Alpine.js podem gerar regressões silenciosas.

### 2.2. Decisão Arquitetural

Conforme **ADR-006** (Frontend: HTMX + Alpine.js + Tailwind + Jinja2) e **ADR-007** (Qualidade de Software: pytest, 90% cobertura, CI/CD), o Playwright foi escolhido por:

- Manter o ecossistema 100% Python (sem JavaScript obrigatório como Cypress).
- Plugin nativo `pytest-playwright` — integra-se à estrutura `tests/` existente.
- Suporta `async def` nativamente — compatível com `asyncio_mode = "auto"` já configurado.
- Controla browser real — HTMX faz requests HTTP reais, Alpine.js executa no V8.

### 2.3. Premissas

- Testes E2E **não entram na métrica de cobertura** (`--cov-fail-under=90`). Conforme ADR-007, a cobertura é medida sobre o código da aplicação (`toninho/`), não sobre testes.
- Testes E2E rodam em **job separado** no CI — não bloqueiam `make test` nem `make quality`.
- O marker `@pytest.mark.e2e` já está declarado no `pyproject.toml` (campo `markers`).
- O server de teste usa **SQLite** (mesmo padrão de dev) — sem dependência de PostgreSQL para E2E.
- Workers Celery **não são necessários** nesta fase — o foco é validar a UI, não o processamento assíncrono.

---

## 3. Casos de Uso

### UC-01 — Instalar dependências e executar teste de smoke

**Ator:** Desenvolvedor
**Pré-condição:** Projeto clonado, Poetry instalado.
**Fluxo principal:**
1. Executar `poetry add --group dev playwright pytest-playwright`.
2. Executar `playwright install chromium --with-deps`.
3. Executar `make test-e2e`.
4. Teste de smoke navega para `/` e verifica que a página carrega.
5. Teste passa — Playwright está funcional.

**Pós-condição:** Ambiente pronto para implementação dos PRDs 020–025.

---

### UC-02 — Executar testes em modo visível (headed)

**Ator:** Desenvolvedor debugando um teste.
**Pré-condição:** Dependências instaladas (UC-01 concluído).
**Fluxo principal:**
1. Executar `make test-e2e-headed`.
2. Browser Chromium abre visivelmente.
3. Testes executam com slowmo de 300ms entre ações.
4. Desenvolvedor observa o comportamento visualmente.
5. Testes finalizam e browser fecha.

**Pós-condição:** Desenvolvedor identifica visualmente o problema.

---

### UC-03 — Executar um teste específico em modo visível

**Ator:** Desenvolvedor debugando um teste específico.
**Pré-condição:** Dependências instaladas.
**Fluxo principal:**
1. Executar `make test-e2e-headed TEST=tests/e2e/test_uc01_criar_processo.py::test_criar_processo_basico`.
2. Apenas o teste indicado roda com browser visível.

**Pós-condição:** Debugging focado em um cenário.

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos Criados / Alterados

```
tests/e2e/
├── __init__.py                  ← CRIAR: marca como pacote Python
├── conftest.py                  ← CRIAR: fixtures live_server, base_url, helpers
└── test_smoke.py                ← CRIAR: teste de smoke para validar infra

pyproject.toml                   ← ALTERAR: dependências dev + config pytest
Makefile                         ← ALTERAR: novos targets test-e2e e test-e2e-headed
```

### 4.2. Dependências Python (pyproject.toml)

Adicionar ao grupo de dev dependencies:

```toml
[tool.poetry.group.dev.dependencies]
# ... deps existentes ...
playwright = "^1.49.0"
pytest-playwright = "^0.6.2"
```

> `pytest-playwright` fornece automaticamente as fixtures `page`, `browser`, `context` e `base_url` para todos os testes.

### 4.3. Configuração pytest (pyproject.toml)

O marker `e2e` **já existe** no `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: testes unitários",
    "integration: testes de integração",
    "e2e: testes end-to-end com Playwright",
    "slow: testes lentos",
    "requires_redis: testes que requerem Redis",
    "requires_celery: testes que requerem Celery",
]
```

**Alteração necessária** — excluir `tests/e2e/` da cobertura. Adicionar ao `[tool.coverage.run]`:

```toml
[tool.coverage.run]
source = ["toninho"]
omit = [
    "tests/*",
    "migrations/*",
]
```

> Como `source = ["toninho"]` já aponta para o código da app, os testes E2E naturalmente não entram na cobertura. Mas o `omit` explícito garante clareza.

### 4.4. Makefile — Novos Targets

```makefile
# ─── E2E Tests ────────────────────────────────────────────────────────
test-e2e: ## Executa testes E2E com Playwright (headless)
	poetry run pytest tests/e2e/ -m e2e --browser chromium -v

test-e2e-headed: ## Executa testes E2E com browser visível (desenvolvimento/debug)
	poetry run pytest tests/e2e/ -m e2e --browser chromium --headed --slowmo 300 -v

test-e2e-debug: ## Executa teste E2E específico com browser visível
	poetry run pytest $(TEST) -m e2e --browser chromium --headed --slowmo 500 -v -s
```

**Uso:**
```bash
# CI / automatizado (headless)
make test-e2e

# Desenvolvimento — ver o browser executando
make test-e2e-headed

# Debug de um teste específico — slowmo mais alto + print habilitado
make test-e2e-debug TEST=tests/e2e/test_smoke.py
```

### 4.5. conftest.py — Fixtures E2E (tests/e2e/conftest.py)

O `conftest.py` é o coração da infraestrutura E2E. Ele provê:

1. **`live_server`** — sobe um uvicorn com a app FastAPI em uma porta de teste.
2. **`base_url`** — URL base para o Playwright (reconhecida pelo `pytest-playwright`).
3. **`api_client`** — helper para fazer chamadas à API REST (seeding de dados).

```python
"""
Fixtures E2E para testes com Playwright.

Sobe um servidor FastAPI real em processo separado,
com banco SQLite isolado, para testes de browser.
"""

import os
import subprocess
import tempfile
import time
from collections.abc import Generator

import httpx
import pytest

# ─── Configuração ─────────────────────────────────────────────────────

E2E_HOST = "127.0.0.1"
E2E_PORT = 8089
E2E_BASE_URL = f"http://{E2E_HOST}:{E2E_PORT}"
SERVER_STARTUP_TIMEOUT = 30  # segundos


# ─── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def _e2e_db_path() -> Generator[str, None, None]:
    """Cria banco SQLite temporário para a sessão E2E."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="toninho_e2e_")
    os.close(db_fd)
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="session")
def _e2e_env(_e2e_db_path: str) -> dict[str, str]:
    """Variáveis de ambiente para o servidor E2E."""
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{_e2e_db_path}"
    env["DEBUG"] = "false"
    env["LOG_LEVEL"] = "WARNING"
    env["SQL_ECHO"] = "false"
    return env


@pytest.fixture(scope="session")
def _run_migrations(_e2e_env: dict[str, str]) -> None:
    """Executa Alembic migrations no banco E2E."""
    result = subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        env=_e2e_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Falha ao executar migrations:\n{result.stderr}"
        )


@pytest.fixture(scope="session")
def live_server(
    _e2e_env: dict[str, str],
    _run_migrations: None,
) -> Generator[str, None, None]:
    """
    Sobe servidor FastAPI em processo separado para testes E2E.

    Yields:
        str: URL base do servidor (ex: http://127.0.0.1:8089)
    """
    process = subprocess.Popen(
        [
            "poetry", "run", "uvicorn",
            "toninho.main:app",
            "--host", E2E_HOST,
            "--port", str(E2E_PORT),
            "--log-level", "warning",
        ],
        env=_e2e_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _wait_for_server(E2E_BASE_URL, timeout=SERVER_STARTUP_TIMEOUT)
        yield E2E_BASE_URL
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture(scope="session")
def base_url(live_server: str) -> str:
    """
    URL base para o Playwright.

    O pytest-playwright reconhece esta fixture e a usa
    automaticamente em page.goto("/rota-relativa").
    """
    return live_server


@pytest.fixture(scope="session")
def api_client(live_server: str) -> Generator[httpx.Client, None, None]:
    """
    Cliente HTTP para seeding de dados via API REST.

    Uso nos testes:
        def test_algo(api_client, page):
            # Criar dados via API
            resp = api_client.post("/api/v1/processos", json={...})
            processo_id = resp.json()["data"]["id"]

            # Navegar com Playwright
            page.goto(f"/processos/{processo_id}")
    """
    with httpx.Client(base_url=live_server, timeout=30.0) as client:
        yield client


# ─── Helpers ──────────────────────────────────────────────────────────


def _wait_for_server(url: str, timeout: int = 30) -> None:
    """Aguarda o servidor responder ao health check."""
    deadline = time.monotonic() + timeout
    last_error = None

    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{url}/api/v1/health", timeout=2.0)
            if resp.status_code == 200:
                return
        except (httpx.ConnectError, httpx.ReadTimeout) as exc:
            last_error = exc
        time.sleep(0.5)

    raise RuntimeError(
        f"Servidor não respondeu em {timeout}s. "
        f"URL: {url}/api/v1/health. Último erro: {last_error}"
    )
```

### 4.6. Teste de Smoke (tests/e2e/test_smoke.py)

Teste mínimo que valida toda a infraestrutura:

```python
"""
Teste de smoke — valida que a infraestrutura E2E funciona.

Verifica:
- Servidor sobe e responde.
- Playwright conecta e navega.
- Templates Jinja2 renderizam.
- HTMX e Alpine.js carregam.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestSmoke:
    """Testes de smoke para validar infraestrutura Playwright."""

    def test_home_page_loads(self, page: Page) -> None:
        """Página inicial carrega com status 200."""
        response = page.goto("/")
        assert response is not None
        assert response.status == 200

    def test_home_page_has_title(self, page: Page) -> None:
        """Página inicial contém o título do app."""
        page.goto("/")
        expect(page).to_have_title("Toninho")

    def test_dashboard_loads(self, page: Page) -> None:
        """Dashboard carrega corretamente."""
        page.goto("/dashboard")
        expect(page.locator("text=Dashboard")).to_be_visible()

    def test_htmx_is_loaded(self, page: Page) -> None:
        """HTMX está carregado no browser."""
        page.goto("/dashboard")
        htmx_version = page.evaluate("() => htmx.version")
        assert htmx_version is not None

    def test_alpine_is_loaded(self, page: Page) -> None:
        """Alpine.js está carregado no browser."""
        page.goto("/processos/novo")
        # Alpine.js está carregado quando x-data é processado
        page.wait_for_function(
            "() => typeof Alpine !== 'undefined'"
        )

    def test_api_health_from_browser(self, page: Page) -> None:
        """Health check da API acessível pelo browser."""
        response = page.goto("/api/v1/health")
        assert response is not None
        assert response.status == 200

    def test_static_files_served(self, page: Page) -> None:
        """Arquivos estáticos (CSS/JS) carregam sem erro."""
        page.goto("/dashboard")
        # Verificar que não há erros de console para recursos estáticos
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.reload()
        page.wait_for_load_state("networkidle")
        # Nenhum erro JavaScript crítico
        assert not errors, f"Erros no console: {errors}"
```

### 4.7. Pacote Python (tests/e2e/__init__.py)

```python
"""Testes E2E com Playwright para o frontend do Toninho."""
```

---

## 5. Dependências

### 5.1. ADRs Referenciados

| ADR | Relação |
|---|---|
| ADR-001 (Stack Tecnológico) | FastAPI + HTMX + Alpine.js — tecnologias sob teste |
| ADR-004 (Arquitetura em Camadas) | `toninho.main:app` como entry point do live_server |
| ADR-006 (Frontend) | HTMX + Alpine.js + Jinja2 — motivação para E2E com browser real |
| ADR-007 (Qualidade de Software) | pytest, 90% cobertura, markers, CI/CD — integração dos testes E2E |

### 5.2. PRDs Anteriores Impactados

| PRD | Tipo de Impacto |
|---|---|
| PRD-013 (Testes e Qualidade) | Extensão: novos targets no Makefile, novos markers |
| PRD-014 (Setup Frontend) | Templates e static files servidos pelo live_server |

### 5.3. Dependências Externas

| Pacote | Versão | Licença | Observação |
|---|---|---|---|
| `playwright` | ^1.49.0 | Apache 2.0 | Biblioteca principal. `playwright install chromium` baixa ~150 MB |
| `pytest-playwright` | ^0.6.2 | Apache 2.0 | Plugin pytest. Fornece fixtures `page`, `browser`, `context` |

---

## 6. Regras de Negócio

### 6.1. Isolamento de Testes E2E

- Testes E2E **não interferem** no `make test` existente. O target `make test` roda apenas `tests/unit/` e `tests/integration/`.
- Testes E2E usam banco SQLite **isolado** (arquivo temporário), sem afetar `toninho.db`.
- O marker `-m e2e` garante que testes E2E só rodam com targets dedicados.

### 6.2. Modos de Execução

| Modo | Target | Flag Playwright | Uso |
|---|---|---|---|
| Headless | `make test-e2e` | (padrão) | CI/CD, execução rápida |
| Headed | `make test-e2e-headed` | `--headed --slowmo 300` | Desenvolvimento, debugging visual |
| Debug | `make test-e2e-debug TEST=...` | `--headed --slowmo 500 -s` | Debug de teste específico com prints |

### 6.3. Fixture `base_url` e pytest-playwright

O `pytest-playwright` reconhece a fixture `base_url` automaticamente. Quando ela existe:
- `page.goto("/dashboard")` navega para `http://127.0.0.1:8089/dashboard`.
- Não é necessário concatenar URLs manualmente.

### 6.4. Seeding de Dados

Testes que precisam de dados pré-existentes devem usar a fixture `api_client` para criar dados via API REST:

```python
def test_ver_processo(api_client, page):
    # Seed: criar processo via API
    resp = api_client.post("/api/v1/processos", json={"nome": "Teste E2E", "descricao": "..."})
    processo_id = resp.json()["data"]["id"]

    # Test: navegar e validar
    page.goto(f"/processos/{processo_id}")
    expect(page.locator("h1")).to_contain_text("Teste E2E")
```

---

## 7. Casos de Teste

### 7.1. Infraestrutura

- ✅ `poetry install` instala `playwright` e `pytest-playwright` sem erros
- ✅ `playwright install chromium` baixa o browser necessário
- ✅ Servidor sobe na porta 8089 com banco SQLite temporário
- ✅ Health check responde 200 em menos de 30s após startup
- ✅ Servidor termina corretamente quando a sessão de testes encerra

### 7.2. Smoke Tests

- ✅ Página inicial (`/`) carrega com status 200
- ✅ Dashboard (`/dashboard`) renderiza com conteúdo visível
- ✅ HTMX está carregado e acessível via `htmx.version`
- ✅ Alpine.js está carregado e processoForm funciona
- ✅ Arquivos estáticos carregam sem erros no console
- ✅ API health check acessível pelo browser

### 7.3. Modos de Execução

- ✅ `make test-e2e` roda headless e passa
- ✅ `make test-e2e-headed` abre browser visível
- ✅ `make test-e2e-debug TEST=...` roda teste específico com browser visível

---

## 8. Critérios de Aceite

- [ ] `playwright` e `pytest-playwright` estão no `pyproject.toml` como dev dependencies.
- [ ] `make test-e2e` executa testes headless e todos os smoke tests passam.
- [ ] `make test-e2e-headed` abre browser Chromium visível com slowmo.
- [ ] `make test-e2e-debug TEST=<path>` roda teste específico com browser visível.
- [ ] `make test` continua funcionando sem alterações (não executa testes E2E).
- [ ] `make quality` continua passando (E2E não impacta cobertura de 90%).
- [ ] `tests/e2e/conftest.py` sobe servidor FastAPI em processo isolado com banco temporário.
- [ ] Teste de smoke valida: página carrega, HTMX presente, Alpine.js presente.

---

## 9. Notas e Observações

### 9.1. Instalação do Chromium

Na primeira execução, é necessário instalar o browser:

```bash
# Instala Chromium + dependências de sistema
playwright install chromium --with-deps
```

Em CI (GitHub Actions), adicionar step antes dos testes:

```yaml
- name: Install Playwright Browsers
  run: playwright install chromium --with-deps
```

### 9.2. Porta do Servidor de Teste

A porta **8089** foi escolhida para evitar conflito com:
- `8000` — servidor de desenvolvimento (`make run`)
- `8001` — porta alternativa comum

### 9.3. Performance

O overhead de subir o servidor é ~2-5s. Como o `live_server` é `scope="session"`, este custo é pago apenas uma vez por suite de testes, não por teste individual.

### 9.4. Playwright Codegen

Com a infraestrutura pronta, desenvolvedores podem usar `codegen` para gerar rascunhos de testes:

```bash
# Garanta que o servidor está rodando (make run) e execute:
playwright codegen http://localhost:8000
```

### 9.5. Sobre Workers Celery

Neste PRD, o servidor E2E **não inicia workers Celery**. Testes que precisam de execuções em andamento (UC-08, UC-09) criarão dados via API com status pré-definido, sem depender de processamento real. Se no futuro for necessário testar com workers reais, um novo fixture `live_worker` poderá ser adicionado.
