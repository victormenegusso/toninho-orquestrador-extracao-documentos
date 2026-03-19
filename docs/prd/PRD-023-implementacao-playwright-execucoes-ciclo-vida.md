# PRD-023: Implementação Playwright — Execuções: Ciclo de Vida e Listagem

**Status**: 📋 Planejado
**Prioridade**: 🔴 Alta — Controle operacional de execuções
**Categoria**: Testing — E2E Frontend
**Estimativa**: 4-5 horas
**Depende de**: PRD-019 (infraestrutura), PRD-020 (fixtures de seeding)

---

## 1. Objetivo

Implementar testes E2E para o **ciclo de vida de execuções** (pausar, retomar, cancelar) e a **listagem de execuções** com filtros. Cobre UC-09 (pausar/retomar/cancelar) e UC-10 (listar/filtrar execuções) do documento de casos de uso E2E.

Estes testes validam:
- Botões condicionais na página de detalhe baseados no status (renderização Jinja2).
- `hx-post` com `hx-confirm` para ações de controle.
- Transições de estado: `em_execucao → pausado → em_execucao → cancelado`.
- Badges de status com cores corretas na listagem.

---

## 2. Contexto e Justificativa

### 2.1. Botões Condicionais por Status

A página de detalhe de execução (`/execucoes/{id}`) renderiza botões condicionais via Jinja2:

| Status da Execução | Botão Pausar | Botão Retomar | Botão Cancelar |
|---|---|---|---|
| `em_execucao` | ✅ Visível (amarelo) | ❌ Oculto | ✅ Visível (vermelho) |
| `pausado` | ❌ Oculto | ✅ Visível (verde) | ✅ Visível (vermelho) |
| `aguardando` | ❌ Oculto | ❌ Oculto | ✅ Visível (vermelho) |
| `concluido` | ❌ Oculto | ❌ Oculto | ❌ Oculto |
| `falhou` | ❌ Oculto | ❌ Oculto | ❌ Oculto |
| `cancelado` | ❌ Oculto | ❌ Oculto | ❌ Oculto |

### 2.2. Ações HTMX

| Ação | Atributos HTMX | Endpoint |
|---|---|---|
| Pausar | `hx-post="/api/v1/execucoes/{id}/pausar"` + `hx-confirm="Pausar esta execução?"` + `hx-swap="none"` | POST `/api/v1/execucoes/{id}/pausar` |
| Retomar | `hx-post="/api/v1/execucoes/{id}/retomar"` + `hx-swap="none"` | POST `/api/v1/execucoes/{id}/retomar` |
| Cancelar | `hx-post="/api/v1/execucoes/{id}/cancelar"` + `hx-confirm="Tem certeza que deseja cancelar esta execução?"` + `hx-swap="none"` | POST `/api/v1/execucoes/{id}/cancelar` |

### 2.3. ADRs Referenciados

| ADR | Relação |
|---|---|
| ADR-006 (Frontend) | HTMX para ações, Jinja2 para renderização condicional |
| ADR-007 (Qualidade) | Testes com pytest e markers |

---

## 3. Casos de Uso

### UC-09 — Pausar, retomar e cancelar execução

**Ator:** Usuário do Toninho
**Pré-condição:** Execução com status `em_execucao`.

**Fluxo principal — Pausar:**
1. Criar processo + configuração + execução via API (seeding).
2. Atualizar status da execução para `em_execucao` via API PATCH.
3. Navegar para `/execucoes/{id}`.
4. Verificar que botão **"Pausar"** está visível (borda amarela).
5. Verificar que botão **"Cancelar"** está visível (borda vermelha).
6. Verificar que botão **"Retomar"** **não** está visível.
7. Clicar "Pausar" → aceitar confirmação `"Pausar esta execução?"`.
8. Interceptar `POST /api/v1/execucoes/{id}/pausar`.
9. Recarregar a página e verificar status `pausado`.

**Fluxo principal — Retomar:**
10. Na página recarregada, verificar que botão **"Retomar"** está visível (borda verde).
11. Verificar que botão **"Pausar"** **não** está visível.
12. Clicar "Retomar".
13. Interceptar `POST /api/v1/execucoes/{id}/retomar`.
14. Recarregar e verificar status `em_execucao`.

**Fluxo principal — Cancelar:**
15. Clicar "Cancelar" → aceitar confirmação `"Tem certeza que deseja cancelar esta execução?"`.
16. Interceptar `POST /api/v1/execucoes/{id}/cancelar`.
17. Recarregar e verificar status `cancelado`.
18. Verificar que **nenhum** botão de controle está visível.

---

### UC-10 — Listar e filtrar execuções

**Ator:** Usuário do Toninho
**Pré-condição:** Execuções com status variados.

**Fluxo principal:**
1. Criar execuções com status distintos via API.
2. Navegar para `/execucoes`.
3. Verificar que a tabela exibe execuções com colunas: ID, Status, Páginas, Taxa de Erro, Início, Duração.
4. Verificar badges de status com cores corretas.
5. Clicar no filtro `"em_execucao"`.
6. Verificar que URL muda para `/execucoes?status=em_execucao`.
7. Verificar que apenas execuções com status correspondente aparecem.
8. Clicar em "Todos" para limpar filtro.
9. Clicar em "Ver detalhes" de uma execução → navega para `/execucoes/{id}`.

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos

```
tests/e2e/
├── conftest.py                           ← ALTERAR: adicionar fixture de seeding de execuções
├── test_uc09_ciclo_vida_execucao.py      ← CRIAR: testes UC-09
└── test_uc10_listagem_execucoes.py       ← CRIAR: testes UC-10
```

### 4.2. Fixture de Seeding de Execuções (tests/e2e/conftest.py)

Adicionar ao `conftest.py`:

```python
@pytest.fixture
def create_execucao(api_client: httpx.Client, create_processo_com_config):
    """
    Factory fixture para criar execução via API REST.

    Cria processo + config automaticamente se não fornecidos.
    Retorna dict com dados da execução.
    """

    def _create(processo_id: str | None = None, **kwargs) -> dict:
        if processo_id is None:
            processo, _ = create_processo_com_config()
            processo_id = processo["id"]

        resp = api_client.post(
            f"/api/v1/processos/{processo_id}/execucoes",
            json=kwargs,
        )
        assert resp.status_code == 201, f"Falha ao criar execução: {resp.text}"
        return resp.json()["data"]

    return _create


@pytest.fixture
def update_execucao_status(api_client: httpx.Client):
    """
    Helper para alterar o status de uma execução via API PATCH.
    """

    def _update(execucao_id: str, status: str) -> dict:
        resp = api_client.patch(
            f"/api/v1/execucoes/{execucao_id}/status",
            json={"status": status},
        )
        assert resp.status_code == 200, f"Falha ao atualizar status: {resp.text}"
        return resp.json()["data"]

    return _update
```

### 4.3. Seletores de Elementos — Detalhe de Execução

| Elemento | Seletor Playwright |
|---|---|
| Botão Pausar | `page.locator("button:has-text('Pausar')")` |
| Botão Retomar | `page.locator("button:has-text('Retomar')")` |
| Botão Cancelar | `page.locator("button:has-text('Cancelar')")` |
| Status badge | `page.locator(".inline-flex.items-center.rounded-full")` |
| Progress section | `page.locator("#progress-section")` |

### 4.4. Seletores de Elementos — Listagem de Execuções

| Elemento | Seletor Playwright |
|---|---|
| Filtro "Todos" | `page.locator("a:has-text('Todos')").first` |
| Filtro por status | `page.locator(f"a[href='/execucoes?status={status}']")` |
| Tabela de execuções | `page.locator("table")` |
| Link "Ver detalhes" | `page.locator("a:has-text('Ver detalhes')").first` |
| Badge concluido | `page.locator(".bg-green-100.text-green-800")` |
| Badge em_execucao | `page.locator(".bg-blue-100.text-blue-800")` |
| Badge falhou | `page.locator(".bg-red-100.text-red-800")` |
| Badge pausado | `page.locator(".bg-yellow-100.text-yellow-800")` |

### 4.5. Exemplo de Teste — Ciclo de Vida Completo

```python
"""Testes E2E — UC-09: Ciclo de vida de execução."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestCicloVidaExecucao:
    """Testes para pausar, retomar e cancelar execuções."""

    def test_botoes_visiveis_em_execucao(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        """Execução em andamento mostra Pausar e Cancelar."""
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        page.goto(f"/execucoes/{execucao_id}")

        expect(page.locator("button:has-text('Pausar')")).to_be_visible()
        expect(page.locator("button:has-text('Cancelar')")).to_be_visible()
        expect(page.locator("button:has-text('Retomar')")).not_to_be_visible()

    def test_pausar_execucao(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        """Pausar execução via HTMX com confirmação."""
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        page.goto(f"/execucoes/{execucao_id}")

        # Aceitar diálogo de confirmação
        page.on("dialog", lambda dialog: dialog.accept())

        with page.expect_response(f"**/api/v1/execucoes/{execucao_id}/pausar"):
            page.locator("button:has-text('Pausar')").click()

        # Recarregar e verificar novo estado
        page.reload()
        expect(page.locator("button:has-text('Retomar')")).to_be_visible()
        expect(page.locator("button:has-text('Pausar')")).not_to_be_visible()

    def test_botoes_ocultos_estado_terminal(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        """Estados terminais não mostram botões de controle."""
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "concluido")

        page.goto(f"/execucoes/{execucao_id}")

        expect(page.locator("button:has-text('Pausar')")).not_to_be_visible()
        expect(page.locator("button:has-text('Retomar')")).not_to_be_visible()
        expect(page.locator("button:has-text('Cancelar')")).not_to_be_visible()
```

### 4.6. Exemplo de Teste — Listagem com Filtros

```python
"""Testes E2E — UC-10: Listagem e filtro de execuções."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestListagemExecucoes:
    """Testes para listagem e filtro de execuções."""

    def test_tabela_exibe_execucoes(
        self, page: Page, create_execucao
    ) -> None:
        """Tabela exibe execuções criadas."""
        create_execucao()
        page.goto("/execucoes")

        expect(page.locator("table")).to_be_visible()
        expect(page.locator("a:has-text('Ver detalhes')").first).to_be_visible()

    def test_filtro_por_status(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        """Filtro por status mostra apenas execuções correspondentes."""
        exec1 = create_execucao()
        update_execucao_status(exec1["id"], "concluido")

        page.goto("/execucoes?status=concluido")
        page.wait_for_load_state("networkidle")

        # Badge verde deve estar visível
        expect(page.locator(".bg-green-100").first).to_be_visible()

    def test_link_ver_detalhes(self, page: Page, create_execucao) -> None:
        """Link 'Ver detalhes' navega para página da execução."""
        execucao = create_execucao()
        page.goto("/execucoes")

        page.locator("a:has-text('Ver detalhes')").first.click()
        page.wait_for_url("**/execucoes/*")
```

---

## 5. Dependências

### 5.1. PRDs Anteriores

| PRD | Dependência |
|---|---|
| PRD-019 | **Obrigatório** — infraestrutura, live_server |
| PRD-020 | **Obrigatório** — `create_processo_com_config` para seeding |
| PRD-007 | Módulo Execução — regras de transição de status |
| PRD-016 | Interface de Monitoramento — templates sob teste |

### 5.2. Endpoints da API Utilizados

| Método | Endpoint | Uso |
|---|---|---|
| POST | `/api/v1/processos/{id}/execucoes` | Criar execução (seeding) |
| PATCH | `/api/v1/execucoes/{id}/status` | Alterar status (seeding para estados específicos) |
| POST | `/api/v1/execucoes/{id}/pausar` | Pausar (testado via HTMX) |
| POST | `/api/v1/execucoes/{id}/retomar` | Retomar (testado via HTMX) |
| POST | `/api/v1/execucoes/{id}/cancelar` | Cancelar (testado via HTMX) |
| GET | `/execucoes` | Listagem (navegação) |

---

## 6. Regras de Negócio

### 6.1. Transições de Status Válidas

O backend valida transições. O frontend só exibe botões para transições válidas:
- `em_execucao` → `pausado` (via Pausar)
- `pausado` → `em_execucao` (via Retomar)
- `em_execucao` / `pausado` / `aguardando` → `cancelado` (via Cancelar)
- Estados terminais (`concluido`, `falhou`, `cancelado`, `concluido_com_erros`) → nenhuma transição.

### 6.2. hx-swap="none"

Todas as ações de controle usam `hx-swap="none"` — o HTMX não altera o DOM com a response. O estado visual é atualizado ao recarregar a página ou via polling (se implementado no PRD-022).

### 6.3. Confirmação Seletiva

- **Pausar**: exige confirmação (`hx-confirm`).
- **Retomar**: **não** exige confirmação (sem `hx-confirm`).
- **Cancelar**: exige confirmação com mensagem mais enfática.

### 6.4. Badges de Status

| Status | Classes CSS |
|---|---|
| `em_execucao` | `bg-blue-100 text-blue-800` |
| `concluido` | `bg-green-100 text-green-800` |
| `falhou` | `bg-red-100 text-red-800` |
| `pausado` | `bg-yellow-100 text-yellow-800` |
| `cancelado` | `bg-gray-100 text-gray-800` |
| `concluido_com_erros` | `bg-gray-100 text-gray-800` |

---

## 7. Casos de Teste

### 7.1. UC-09 — Ciclo de Vida

- ✅ Execução `em_execucao`: Pausar e Cancelar visíveis, Retomar oculto
- ✅ Clicar Pausar → confirmação → POST pausar → recarregar → status `pausado`
- ✅ Execução `pausado`: Retomar e Cancelar visíveis, Pausar oculto
- ✅ Clicar Retomar → POST retomar (sem confirmação) → recarregar → status `em_execucao`
- ✅ Clicar Cancelar → confirmação enfática → POST cancelar → recarregar → status `cancelado`
- ✅ Estados terminais (`concluido`, `falhou`, `cancelado`): nenhum botão de controle visível
- ✅ Transição completa: `em_execucao → pausado → em_execucao → cancelado`

### 7.2. UC-10 — Listagem

- ✅ Tabela exibe colunas: ID, Status, Páginas, Taxa de Erro, Início, Duração
- ✅ Badges de status com cores corretas
- ✅ Filtro por status filtra via query param
- ✅ Filtro "Todos" limpa filtro
- ✅ Link "Ver detalhes" navega para `/execucoes/{id}`
- ✅ Paginação funcional (se houver dados suficientes)

---

## 8. Critérios de Aceite

- [ ] Botões Pausar/Retomar/Cancelar aparecem condicionalmente conforme status.
- [ ] Pausar e Cancelar exigem confirmação; Retomar não.
- [ ] Transições de estado refletidas corretamente após recarregar.
- [ ] Estados terminais não exibem botões de controle.
- [ ] Listagem de execuções exibe tabela com badges coloridos.
- [ ] Filtro por status funciona via query params.
- [ ] Link "Ver detalhes" navega corretamente.
- [ ] Todos os testes passam com `make test-e2e`.

---

## 9. Notas e Observações

### 9.1. Seeding de Status

O endpoint PATCH `/api/v1/execucoes/{id}/status` permite alterar o status diretamente. Isso é essencial para testes que precisam de execuções em estados específicos sem depender de workers Celery.

### 9.2. Reload após Ação

Como `hx-swap="none"` não atualiza o DOM, os testes fazem `page.reload()` após cada ação para verificar o novo estado. Em uso real, o usuário veria o status atualizado via polling ou navegação.

### 9.3. Teste de Ciclo Completo

O teste mais importante é o ciclo completo: `em_execucao → pausado → em_execucao → cancelado`. Pode ser implementado como um único teste sequencial ou como testes individuais — preferir testes individuais para melhor isolamento e diagnóstico de falhas.
