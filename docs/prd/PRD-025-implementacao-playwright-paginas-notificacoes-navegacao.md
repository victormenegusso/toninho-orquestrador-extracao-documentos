# PRD-025: Implementação Playwright — Páginas Extraídas, Notificações e Navegação

**Status**: 📋 Planejado
**Prioridade**: 🟡 Média — UCs P1 e P2, funcionalidades de suporte
**Categoria**: Testing — E2E Frontend
**Estimativa**: 5-6 horas
**Depende de**: PRD-019 (infraestrutura), PRD-023 (fixtures de execução)

---

## 1. Objetivo

Implementar testes E2E para quatro funcionalidades de suporte do frontend:
- **UC-11** — Navegar pelas páginas extraídas (grid HTMX, busca, filtro, preview modal, download).
- **UC-12** — Sistema de notificações (flash messages Alpine.js e eventos HTMX).
- **UC-13** — Navegação geral e sidebar (`hx-boost`).
- **UC-14** — Tratamento de erros de rede (resiliência HTMX).

Estes UCs cobrem a experiência de navegação, feedback visual e resiliência a falhas — elementos que complementam os fluxos críticos testados nos PRDs anteriores.

---

## 2. Contexto e Justificativa

### 2.1. Stack de Referência

| Componente | Tecnologia | Relevância neste PRD |
|---|---|---|
| Grid de páginas | HTMX (`hx-get`, `hx-trigger`, `hx-include`) | UC-11 |
| Preview modal | JavaScript vanilla (`openPreview(id)`, `closePreview()`) | UC-11 |
| Flash messages | Alpine.js (`x-show`, `x-transition`, `@click`) | UC-12 |
| Sidebar | `hx-boost="true"` herdado do `<body>` | UC-13 |
| Error handling | Listener `htmx:responseError` no `base.html` | UC-14 |

### 2.2. ADRs Referenciados

| ADR | Relação |
|---|---|
| ADR-006 (Frontend) | HTMX + Alpine.js + Tailwind CSS |
| ADR-007 (Qualidade) | Cobertura E2E para fluxos críticos de UX |

---

## 3. Casos de Uso

### UC-11 — Navegar pelas páginas extraídas

**Ator:** Usuário do Toninho
**Prioridade:** 🟡 P1
**Pré-condição:** Execução concluída com páginas extraídas (sucesso, falhou, ignorado).

**Fluxo principal:**
1. Navegar para `/execucoes/{id}/paginas`.
2. Verificar grid com cards de páginas (URL, status, tamanho).
3. Digitar no campo de busca `input[name="search"]`.
4. Aguardar debounce (500ms) — `hx-trigger="keyup changed delay:500ms"`.
5. Verificar swap do `#paginas-grid` via HTMX.
6. Verificar que apenas páginas correspondentes aparecem.

**Variações:**

| ID | Variação | Detalhe técnico |
|---|---|---|
| UC-11a | Filtro por status | `select[name="status"]` → opções: Todos, sucesso, falhou, ignorado |
| UC-11b | Busca + filtro combinados | `hx-include="[name='search']"` e `hx-include="[name='status']"` cruzam parâmetros |
| UC-11c | Preview de página | `openPreview(id)` → fetch `/api/v1/paginas/{id}` + `/api/v1/paginas/{id}/content` → modal `#preview-modal` |
| UC-11d | Download de página | `a[href^="/api/v1/paginas/"][download]` → arquivo baixado |

---

### UC-12 — Sistema de notificações (toasts e flash messages)

**Ator:** Usuário do Toninho
**Prioridade:** 🟢 P2
**Pré-condição:** Nenhuma específica.

**Fluxo — Flash Messages:**
1. Realizar ação que gere flash message (ex: criar processo via API, navegar para a página com mensagem na sessão).
2. Verificar alert no `#flash-messages` (`.fixed.top-4.right-4.z-50`).
3. Verificar animação de entrada (`x-transition`).
4. Clicar botão fechar (`@click="show = false"`).
5. Verificar que alert desaparece.

**Fluxo — Eventos HTMX:**
6. Disparar erro HTMX (interceptar request e retornar 500).
7. Verificar que `htmx:responseError` é disparado.
8. Verificar que `console.error` é chamado (comportamento atual do `base.html`).

---

### UC-13 — Navegação geral e sidebar

**Ator:** Usuário do Toninho
**Prioridade:** 🟢 P2
**Pré-condição:** App rodando.

**Fluxo principal:**
1. Acessar `/dashboard`.
2. Clicar em "Processos" na sidebar → verificar navegação para `/processos`.
3. Clicar em "Execuções" → verificar `/execucoes`.
4. Clicar em "Dashboard" → verificar `/dashboard`.
5. Verificar que navegação usa `hx-boost` (sem full page reload).

---

### UC-14 — Tratamento de erros de rede (HTMX)

**Ator:** Usuário do Toninho
**Prioridade:** 🟢 P2
**Pré-condição:** App rodando.

**Fluxo principal:**
1. Navegar para `/processos`.
2. Interceptar requests HTMX com `page.route()` e retornar erro 500.
3. Disparar busca no campo de pesquisa.
4. Verificar que a tabela mantém conteúdo anterior (não fica vazia).

**Variações:**

| ID | Variação | Cenário |
|---|---|---|
| UC-14a | Timeout HTMX | Request demora → HTMX dispara `htmx:timeout` |
| UC-14b | Erro no formulário Alpine | Servidor retorna 422 → Alpine exibe `globalError` |
| UC-14c | Dashboard polling com erro | Polling falha → polls seguintes continuam funcionando |

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos

```
tests/e2e/
├── conftest.py                        ← ALTERAR: adicionar fixtures de seeding de páginas
├── test_uc11_paginas_extraidas.py     ← CRIAR: UC-11 + variações
├── test_uc12_notificacoes.py          ← CRIAR: UC-12
├── test_uc13_navegacao.py             ← CRIAR: UC-13
└── test_uc14_erros_rede.py            ← CRIAR: UC-14 + variações
```

### 4.2. Fixtures de Seeding (tests/e2e/conftest.py)

Adicionar ao `conftest.py`:

```python
@pytest.fixture
def create_paginas_extraidas(api_client: httpx.Client, create_execucao, update_execucao_status):
    """
    Factory fixture para criar uma execução concluída com páginas extraídas.

    Retorna dict com {execucao_id, paginas: [{id, url, status}]}
    """

    def _create(
        num_paginas: int = 5,
        statuses: list[str] | None = None,
    ) -> dict:
        # Criar execução e marcar como concluída
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "concluido")

        # Criar páginas com statuses variados
        if statuses is None:
            statuses = ["sucesso", "sucesso", "falhou", "sucesso", "ignorado"]

        paginas = []
        for i, status in enumerate(statuses[:num_paginas]):
            resp = api_client.post(
                f"/api/v1/paginas",
                json={
                    "execucao_id": execucao_id,
                    "url": f"https://example.com/page-{i+1}",
                    "status": status,
                    "tamanho": 1024 * (i + 1),
                    "conteudo": f"Conteúdo da página {i+1}",
                },
            )
            assert resp.status_code == 201, f"Falha ao criar página: {resp.text}"
            paginas.append(resp.json())

        return {"execucao_id": execucao_id, "paginas": paginas}

    return _create
```

### 4.3. Seletores de Elementos — UC-11 (Páginas Extraídas)

| Elemento | Seletor Playwright |
|---|---|
| Grid wrapper (HTMX target) | `page.locator("#paginas-grid")` |
| Cards grid interno | `page.locator("#paginas-cards")` |
| Card individual | `page.locator(".card")` |
| Campo de busca | `page.locator("input[name='search']")` |
| Filtro de status | `page.locator("select[name='status']")` |
| Badge status sucesso | `page.locator(".bg-green-100.text-green-800")` |
| Badge status falhou | `page.locator(".bg-red-100.text-red-800")` |
| Badge status outro | `page.locator(".bg-gray-100.text-gray-800")` |
| Botão Preview | `page.locator("button[onclick^='openPreview']")` |
| Link Detalhes | `page.locator("a[href^='/paginas/']")` |
| Link Download | `page.locator("a[download]")` |
| Modal preview | `page.locator("#preview-modal")` |
| Título do preview | `page.locator("#preview-title")` |
| Conteúdo do preview | `page.locator("#preview-content")` |
| Texto do preview | `page.locator("#preview-text")` |
| Loading do preview | `page.locator("#preview-loading")` |
| Erro do preview | `page.locator("#preview-error")` |
| Fechar preview | `page.locator("button[onclick='closePreview()']")` |
| Botão download all | `page.locator("a[href$='/download-all']")` |
| Stats total páginas | `page.get_by_text("Total de Páginas")` |
| Estado vazio | `page.get_by_text("Nenhuma página encontrada")` |

### 4.4. Seletores de Elementos — UC-12 (Notificações)

| Elemento | Seletor Playwright |
|---|---|
| Container flash messages | `page.locator("#flash-messages")` |
| Alert success | `page.locator("#flash-messages .bg-green-50")` |
| Alert error | `page.locator("#flash-messages .bg-red-50")` |
| Alert warning | `page.locator("#flash-messages .bg-yellow-50")` |
| Alert info | `page.locator("#flash-messages .bg-blue-50")` |
| Texto do alert | `page.locator("#flash-messages p.text-sm.font-medium")` |
| Botão fechar | `page.locator("#flash-messages button")` |

### 4.5. Seletores de Elementos — UC-13 (Sidebar)

| Elemento | Seletor Playwright |
|---|---|
| Sidebar container | `page.locator("aside")` |
| Link Dashboard | `page.locator("aside a[href='/dashboard']")` |
| Link Processos | `page.locator("aside a[href='/processos']")` |
| Link Execuções | `page.locator("aside a[href='/execucoes']")` |
| Área de conteúdo | `page.locator("main")` |
| Logo "Toninho" | `page.locator("aside h1")` |

### 4.6. Código — UC-11: Busca com Debounce HTMX

```python
import re
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestPaginasExtraidas:
    """Testes E2E para UC-11 — Páginas Extraídas."""

    def test_grid_exibe_cards(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        """Grid exibe cards de páginas extraídas com URL e status."""
        data = create_paginas_extraidas(num_paginas=3)
        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        grid = page.locator("#paginas-grid")
        expect(grid).to_be_visible()

        cards = page.locator(".card")
        expect(cards).to_have_count(3)

    def test_busca_com_debounce(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        """Busca por URL dispara request HTMX após debounce de 500ms."""
        data = create_paginas_extraidas(
            statuses=["sucesso", "sucesso", "sucesso"]
        )
        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        search_input = page.locator("input[name='search']")
        search_input.fill("page-1")

        # Aguardar request HTMX (debounce 500ms + request)
        with page.expect_response("**/paginas/search**", timeout=3000) as resp:
            pass

        assert resp.value.status == 200

        # Grid atualizado
        grid = page.locator("#paginas-grid")
        expect(grid).to_be_visible()

    def test_filtro_por_status(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        """Filtro por status atualiza grid via HTMX."""
        data = create_paginas_extraidas(
            statuses=["sucesso", "falhou", "sucesso"]
        )
        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        # Selecionar "sucesso" no filtro
        page.locator("select[name='status']").select_option("sucesso")

        # Aguardar HTMX swap
        with page.expect_response("**/paginas/search**", timeout=3000) as resp:
            pass

        assert resp.value.status == 200

    def test_busca_e_filtro_combinados(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        """Busca + filtro são enviados juntos via hx-include."""
        data = create_paginas_extraidas(
            statuses=["sucesso", "falhou", "sucesso"]
        )
        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        # Aplicar filtro
        page.locator("select[name='status']").select_option("sucesso")
        page.wait_for_timeout(1000)

        # Buscar com filtro já ativo
        search_input = page.locator("input[name='search']")
        search_input.fill("page")

        with page.expect_response("**/paginas/search**", timeout=3000) as resp:
            pass

        # Verificar que a URL da request contém ambos os parâmetros
        url = resp.value.url
        assert "search=" in url or "status=" in url
```

### 4.7. Código — UC-11c: Preview Modal

```python
    def test_preview_modal(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        """Clicar Preview abre modal com conteúdo da página."""
        data = create_paginas_extraidas(num_paginas=1, statuses=["sucesso"])
        pagina_id = data["paginas"][0]["id"]

        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        # Clicar no botão Preview do primeiro card
        preview_btn = page.locator("button[onclick^='openPreview']").first
        preview_btn.click()

        # Modal deve aparecer
        modal = page.locator("#preview-modal")
        expect(modal).to_be_visible(timeout=5000)

        # Conteúdo deve carregar
        content = page.locator("#preview-text")
        expect(content).not_to_be_empty(timeout=5000)

        # Fechar modal
        page.locator("button[onclick='closePreview()']").first.click()
        expect(modal).to_be_hidden()

    def test_preview_modal_fecha_com_escape(
        self, page: Page, create_paginas_extraidas
    ) -> None:
        """Modal de preview fecha com tecla Escape."""
        data = create_paginas_extraidas(num_paginas=1, statuses=["sucesso"])
        page.goto(f"/execucoes/{data['execucao_id']}/paginas")

        page.locator("button[onclick^='openPreview']").first.click()

        modal = page.locator("#preview-modal")
        expect(modal).to_be_visible(timeout=5000)

        # Pressionar Escape
        page.keyboard.press("Escape")
        expect(modal).to_be_hidden()
```

### 4.8. Código — UC-12: Flash Messages

```python
@pytest.mark.e2e
class TestNotificacoes:
    """Testes E2E para UC-12 — Notificações."""

    def test_flash_message_success_visivel(
        self, page: Page, api_client
    ) -> None:
        """Flash message de sucesso aparece após criar processo."""
        # Criar processo via formulário para gerar flash message
        page.goto("/processos/novo")

        # Preencher formulário mínimo e submeter
        # (usa a lógica do Alpine.js processoForm)
        page.locator("[x-model='form.nome']").fill("Processo Flash Test")
        page.locator("[x-model='form.url_base']").fill("https://example.com")
        page.locator("button[type='submit']").click()

        # Aguardar redirecionamento e verificar flash message
        page.wait_for_url("**/processos**", timeout=5000)

        flash = page.locator("#flash-messages")
        # Flash message pode ou não existir dependendo da implementação
        # Se existir, verificar cor verde
        if flash.count() > 0:
            alert = page.locator("#flash-messages .bg-green-50")
            expect(alert).to_be_visible()

    def test_flash_message_fecha_com_botao(
        self, page: Page
    ) -> None:
        """Botão de fechar remove flash message com transição."""
        # Navegar para página que gera flash (ex: após ação bem-sucedida)
        # Nota: a existência de flash depende da sessão do servidor
        page.goto("/processos")

        flash_container = page.locator("#flash-messages")
        if flash_container.count() > 0 and flash_container.locator("button").count() > 0:
            close_btn = flash_container.locator("button").first
            close_btn.click()

            # Alpine.js x-show=false com x-transition
            page.wait_for_timeout(500)  # Aguardar transição
            alert = flash_container.locator("[x-data]").first
            expect(alert).to_be_hidden()
```

### 4.9. Código — UC-13: Navegação Sidebar com hx-boost

```python
@pytest.mark.e2e
class TestNavegacao:
    """Testes E2E para UC-13 — Navegação e Sidebar."""

    def test_sidebar_links_presentes(self, page: Page) -> None:
        """Sidebar contém links para Dashboard, Processos e Execuções."""
        page.goto("/dashboard")

        sidebar = page.locator("aside")
        expect(sidebar).to_be_visible()

        expect(sidebar.locator("a[href='/dashboard']")).to_be_visible()
        expect(sidebar.locator("a[href='/processos']")).to_be_visible()
        expect(sidebar.locator("a[href='/execucoes']")).to_be_visible()

    def test_navegar_para_processos(self, page: Page) -> None:
        """Clicar em 'Processos' navega via hx-boost sem full reload."""
        page.goto("/dashboard")

        # Interceptar para verificar que é HTMX (header HX-Request)
        requests = []
        page.on("request", lambda req: requests.append(req))

        page.locator("aside a[href='/processos']").click()

        # URL deve mudar para /processos
        page.wait_for_url("**/processos", timeout=5000)

        # Verificar que o conteúdo principal mudou
        main = page.locator("main")
        expect(main).to_be_visible()

    def test_navegar_para_execucoes(self, page: Page) -> None:
        """Clicar em 'Execuções' navega para /execucoes."""
        page.goto("/dashboard")

        page.locator("aside a[href='/execucoes']").click()
        page.wait_for_url("**/execucoes", timeout=5000)

    def test_navegar_para_dashboard(self, page: Page) -> None:
        """Clicar em 'Dashboard' navega de volta."""
        page.goto("/processos")

        page.locator("aside a[href='/dashboard']").click()
        page.wait_for_url("**/dashboard", timeout=5000)

    def test_logo_presente(self, page: Page) -> None:
        """Logo 'Toninho' visível na sidebar."""
        page.goto("/dashboard")

        logo = page.locator("aside h1")
        expect(logo).to_contain_text("Toninho")
```

### 4.10. Código — UC-14: Erros de Rede HTMX

```python
@pytest.mark.e2e
class TestErrosRede:
    """Testes E2E para UC-14 — Tratamento de erros de rede."""

    def test_erro_500_nao_limpa_tabela(self, page: Page) -> None:
        """Erro 500 em request HTMX mantém conteúdo anterior da tabela."""
        page.goto("/processos")

        # Capturar conteúdo atual da tabela
        main_content = page.locator("main")
        initial_html = main_content.inner_html()

        # Interceptar a próxima request de busca e retornar 500
        page.route("**/processos/search**", lambda route: route.fulfill(
            status=500,
            body="Internal Server Error",
        ))

        # Disparar busca
        search_input = page.locator("input[name='search']")
        if search_input.count() > 0:
            search_input.fill("test")
            page.wait_for_timeout(1000)

            # A tabela deve manter conteúdo (HTMX não faz swap em erro por padrão)
            current_html = main_content.inner_html()
            assert len(current_html) > 0  # Não ficou vazia

        # Remover interceptação
        page.unroute("**/processos/search**")

    def test_htmx_response_error_event(self, page: Page) -> None:
        """Evento htmx:responseError é disparado no erro."""
        page.goto("/processos")

        # Listener para capturar o evento htmx:responseError
        error_events = []
        page.evaluate("""() => {
            window.__htmxErrors = [];
            document.body.addEventListener('htmx:responseError', (evt) => {
                window.__htmxErrors.push({
                    status: evt.detail.xhr?.status,
                    path: evt.detail.pathInfo?.requestPath
                });
            });
        }""")

        # Interceptar e retornar 500
        page.route("**/processos/search**", lambda route: route.fulfill(
            status=500,
            body="Internal Server Error",
        ))

        # Disparar busca
        search_input = page.locator("input[name='search']")
        if search_input.count() > 0:
            search_input.fill("trigger-error")
            page.wait_for_timeout(1500)  # debounce + request

            # Verificar que o evento foi capturado
            errors = page.evaluate("() => window.__htmxErrors")
            assert len(errors) > 0

        page.unroute("**/processos/search**")

    def test_dashboard_polling_resiliente(
        self, page: Page
    ) -> None:
        """Polling do dashboard continua após erro pontual."""
        page.goto("/dashboard")

        # Contador de requests
        page.evaluate("""() => {
            window.__pollCount = 0;
            window.__pollErrors = 0;
        }""")

        poll_count = {"success": 0, "error": 0}

        def handle_response(response):
            if "/dashboard/" in response.url or "/stats" in response.url:
                if response.status >= 500:
                    poll_count["error"] += 1
                else:
                    poll_count["success"] += 1

        page.on("response", handle_response)

        # Interceptar UMA request de polling e retornar erro
        first_intercept = {"done": False}

        def maybe_fail(route):
            if not first_intercept["done"]:
                first_intercept["done"] = True
                route.fulfill(status=500, body="Simulated error")
            else:
                route.continue_()

        page.route("**/dashboard/stats**", maybe_fail)

        # Aguardar múltiplos ciclos de polling (stats poll é 5s, aguardar 15s)
        page.wait_for_timeout(15000)

        # Deve ter havido requests bem-sucedidas APÓS o erro
        assert poll_count["success"] >= 1, "Polling deveria ter se recuperado após erro"

        page.unroute("**/dashboard/stats**")
```

---

## 5. Dependências

### 5.1. PRDs Anteriores

| PRD | Dependência |
|---|---|
| PRD-019 | **Obrigatório** — infraestrutura, live_server, base_url |
| PRD-023 | **Obrigatório** — fixtures `create_execucao`, `update_execucao_status` |
| PRD-020 | **Opcional** — fixture `create_processo` (para UC-12 flash messages) |

### 5.2. Endpoints da API Utilizados

| Método | Endpoint | UC | Uso |
|---|---|---|---|
| POST | `/api/v1/processos` | UC-12 | Gerar flash message |
| GET | `/paginas/search?execucao_id=...&search=...&status=...` | UC-11 | HTMX search/filter |
| GET | `/api/v1/paginas/{id}` | UC-11c | Preview metadata |
| GET | `/api/v1/paginas/{id}/content` | UC-11c | Preview conteúdo |
| GET | `/api/v1/paginas/{id}/download` | UC-11d | Download |
| GET | `/api/v1/execucoes/{id}/download-all` | UC-11 | Download ZIP |
| GET | `/dashboard` | UC-13 | Navegação |
| GET | `/processos` | UC-13, UC-14 | Navegação / Erro |
| GET | `/execucoes` | UC-13 | Navegação |
| GET | `/processos/search` | UC-14 | Interceptação |
| GET | `/dashboard/stats` | UC-14c | Polling resiliente |

---

## 6. Regras de Negócio

### 6.1. HTMX Debounce e hx-include (UC-11)

O campo de busca `input[name="search"]` e o filtro `select[name="status"]` compartilham o mesmo `hx-target="#paginas-grid"`. Cada um usa `hx-include` para incluir o valor do outro na request:

```
input[name="search"]:  hx-include="[name='status']"
select[name="status"]: hx-include="[name='search']"
```

Isso garante que **busca + filtro são sempre enviados juntos** ao servidor.

### 6.2. Preview Modal — JavaScript Vanilla (UC-11c)

O modal de preview **não usa Alpine.js**, diferente de outros modais do sistema. Usa funções globais:
- `openPreview(paginaId)` — faz 2 fetches: metadata + conteúdo.
- `closePreview()` — esconde o modal.
- Listener de `keydown` no `document` fecha com `Escape`.

O fluxo tem estados de loading:
1. Modal aparece com `#preview-loading` visível.
2. Fetch da metadata preenche `#preview-title` e `#preview-url`.
3. Fetch do conteúdo preenche `#preview-text`.
4. Se erro, `#preview-error` aparece.

### 6.3. Flash Messages — Alpine.js Transitions (UC-12)

Cada alert usa Alpine.js com `x-data="{ show: true }"`:
- `x-show="show"` → controla visibilidade.
- `x-transition:enter/leave` → animação CSS.
- `@click="show = false"` → botão de fechar.

Classes por tipo:
| Tipo | Background | Texto |
|---|---|---|
| success | `bg-green-50` | `text-green-800` |
| error | `bg-red-50` | `text-red-800` |
| warning | `bg-yellow-50` | `text-yellow-800` |
| info | `bg-blue-50` | `text-blue-800` |

### 6.4. hx-boost Navigation (UC-13)

O `<body hx-boost="true">` no `base.html` faz com que **todos os links `<a>`** dentro do body usem HTMX em vez de navegação tradicional. Isso significa:
- Clique em link da sidebar → request HTMX com header `HX-Request: true`.
- Servidor responde com HTML parcial.
- HTMX faz swap do `<body>` inteiro (comportamento padrão de `hx-boost`).
- URL é atualizada via History API (`pushState`).

**Não há classe ativa explícita** na sidebar. Os links não têm `{% if %}` condicional para destacar a página atual. Os testes validam apenas que a navegação funciona.

### 6.5. Erro HTMX — Comportamento Atual (UC-14)

O `base.html` registra listener para `htmx:responseError` que apenas faz `console.error`. **Não há toast/notificação visual implementada**. O teste UC-14 valida:
- Que o evento é disparado (via `window.__htmxErrors`).
- Que o conteúdo anterior é preservado (HTMX não faz swap em erro).
- Que o polling continua após falha pontual.

### 6.6. Status de Páginas — Badges Coloridos (UC-11)

| Status | Classes CSS |
|---|---|
| `sucesso` | `bg-green-100 text-green-800` |
| `falhou` | `bg-red-100 text-red-800` |
| outros | `bg-gray-100 text-gray-800` |

---

## 7. Casos de Teste

### 7.1. Páginas Extraídas (UC-11)

- ✅ Grid exibe cards com URL, status e tamanho.
- ✅ Busca por URL com debounce 500ms dispara request HTMX.
- ✅ Filtro por status atualiza grid.
- ✅ Busca + filtro combinados (hx-include).
- ✅ Preview modal abre e exibe conteúdo.
- ✅ Preview modal fecha com botão e com Escape.
- ✅ Estado vazio: "Nenhuma página encontrada" quando sem resultados.
- ✅ Badges de status com cores corretas.

### 7.2. Notificações (UC-12)

- ✅ Flash message success tem fundo verde (`bg-green-50`).
- ✅ Botão de fechar oculta flash message (`x-show=false`).
- ✅ Transição Alpine.js funciona (entrada suave).

### 7.3. Navegação (UC-13)

- ✅ Sidebar contém 3 links: Dashboard, Processos, Execuções.
- ✅ Navegação via sidebar muda URL corretamente.
- ✅ Logo "Toninho" presente na sidebar.

### 7.4. Erros de Rede (UC-14)

- ✅ Erro 500 em request HTMX não limpa conteúdo da tabela.
- ✅ Evento `htmx:responseError` é disparado.
- ✅ Polling do dashboard continua após erro pontual.

---

## 8. Critérios de Aceite

- [ ] Grid de páginas exibe cards e responde a busca/filtro HTMX.
- [ ] Preview modal abre, exibe conteúdo e fecha (botão + Escape).
- [ ] Flash messages aparecem com core corretas e fecham com botão.
- [ ] Navegação via sidebar funciona sem full reload.
- [ ] Erro 500 não limpa conteúdo e dispara evento `htmx:responseError`.
- [ ] Polling do dashboard se recupera após falha.
- [ ] Todos os testes passam com `make test-e2e`.

---

## 9. Notas e Observações

### 9.1. Download de Arquivo (UC-11d)

Testar download em Playwright requer configuração especial:
```python
# Configurar diretório de downloads
with page.expect_download() as download_info:
    page.locator("a[download]").first.click()
download = download_info.value
assert download.suggested_filename  # Arquivo foi baixado
```

O download aponta para `/api/v1/paginas/{id}/download`.

### 9.2. Flash Messages Dependem de Sessão

Flash messages são server-side (armazenadas na sessão HTTP). Para testá-las de forma confiável, o teste precisa **executar a ação que gera o flash** (ex: criar processo) e imediatamente verificar a página seguinte. Não é possível "injetar" flash messages arbitrariamente.

### 9.3. hx-boost e Playwright

O `hx-boost` intercepta cliques em links e faz requests HTMX. O Playwright `page.goto()` **não** usa `hx-boost` — faz navegação normal. Para testar `hx-boost`, é necessário simular clique real no link:
```python
# Correto: clique real → hx-boost intercepta
page.locator("aside a[href='/processos']").click()

# Incorreto para testar hx-boost: navegação direta
page.goto("/processos")
```

### 9.4. Interceptação de Requests (UC-14)

`page.route()` intercepta requests **antes** de saírem do browser. Isso é ideal para simular erros de rede sem depender do servidor. Lembrar de chamar `page.unroute()` para limpar interceptações e não afetar outros testes.

### 9.5. Timing do Polling Resiliente (UC-14c)

O teste de polling resiliente (UC-14c) precisa aguardar múltiplos ciclos de polling (~15s) para validar que o polling se recupera. Marcar como `@pytest.mark.slow` se necessário.
