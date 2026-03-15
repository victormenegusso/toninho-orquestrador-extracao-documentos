# PRD-021: Implementação Playwright — Listagem, Busca e Ações em Processos

**Status**: 📋 Planejado
**Prioridade**: 🔴 Alta — Fluxos críticos de operação com HTMX
**Categoria**: Testing — E2E Frontend
**Estimativa**: 4-5 horas
**Depende de**: PRD-019 (infraestrutura), PRD-020 (fixtures de seeding)

---

## 1. Objetivo

Implementar testes E2E para a **listagem de processos** e suas ações: busca HTMX com debounce, execução de processo com confirmação e deleção com animação. Cobre UC-04 (busca/filtro), UC-05 (executar) e UC-06 (deletar) do documento de casos de uso E2E.

Estes UCs focam na página `/processos` e no partial `partials/processos_table.html`, testando:
- HTMX search com `hx-trigger="keyup changed delay:500ms"`.
- `hx-include` para envio combinado de parâmetros.
- `hx-confirm` para diálogos de confirmação nativos.
- `hx-delete` com remoção animada de elementos.

---

## 2. Contexto e Justificativa

### 2.1. Interações HTMX sob teste

A tabela de processos tem 4 interações HTMX distintas:

| Interação | Atributos HTMX | Endpoint |
|---|---|---|
| Busca por nome | `hx-get="/processos/search"` + `hx-trigger="keyup changed delay:500ms"` + `hx-target="#processos-table"` | GET `/processos/search?search=...` |
| Filtro por status | `hx-get="/processos/search"` + `hx-trigger="change"` + `hx-include="[name='search']"` | GET `/processos/search?status=...&search=...` |
| Executar processo | `hx-post="/api/v1/processos/{id}/execucoes"` + `hx-confirm="..."` + `hx-swap="none"` | POST `/api/v1/processos/{id}/execucoes` |
| Deletar processo | `hx-delete="/api/v1/processos/{id}"` + `hx-confirm="..."` + `hx-target="#processo-row-{id}"` + `hx-swap="outerHTML swap:0.5s"` | DELETE `/api/v1/processos/{id}` |

### 2.2. ADRs Referenciados

| ADR | Relação |
|---|---|
| ADR-006 (Frontend) | HTMX para requests parciais sem reload — comportamento sob teste |
| ADR-007 (Qualidade) | Estrutura de testes com pytest |

---

## 3. Casos de Uso

### UC-04 — Buscar e filtrar processos (HTMX)

**Ator:** Usuário do Toninho
**Pré-condição:** Pelo menos 3 processos existentes com nomes e status distintos.

**Fluxo principal — Busca por nome:**
1. Criar 3 processos via `api_client` com nomes distintos: `"Alpha"`, `"Beta"`, `"Gamma"`.
2. Navegar para `/processos`.
3. Verificar que a tabela exibe os 3 processos.
4. Digitar `"Alpha"` no campo de busca.
5. Aguardar debounce de 500ms.
6. Interceptar request `GET /processos/search?search=Alpha`.
7. Verificar que a tabela foi atualizada — apenas `"Alpha"` visível.
8. Verificar que `"Beta"` e `"Gamma"` **não** estão visíveis.

**Variações:**

| ID | Variação | Fluxo |
|---|---|---|
| UC-04a | Filtro por status | Criar processos com status `ativo` e `inativo` → selecionar status no dropdown → tabela atualiza via `hx-trigger="change"` |
| UC-04b | Busca + filtro combinados | Digitar texto + selecionar status → `hx-include` envia ambos → tabela filtra por ambos |
| UC-04c | Busca sem resultados | Digitar `"ZZZNAOEXISTE"` → tabela exibe estado vazio |
| UC-04d | Limpar busca | Apagar todo texto do campo → tabela volta a exibir todos os processos |

---

### UC-05 — Executar processo a partir da listagem

**Ator:** Usuário do Toninho
**Pré-condição:** Processo com configuração válida.

**Fluxo principal:**
1. Criar processo com configuração via `create_processo_com_config`.
2. Navegar para `/processos`.
3. Localizar a row do processo na tabela.
4. Clicar no botão "Executar agora" (ícone play).
5. O browser exibe diálogo de confirmação: `"Executar processo 'X' agora?"`.
6. Aceitar o diálogo (via `page.on("dialog", ...)` + `dialog.accept()`).
7. Interceptar request `POST /api/v1/processos/{id}/execucoes`.
8. Verificar status 201 da response.

**Variações:**

| ID | Variação | O que muda |
|---|---|---|
| UC-05a | Cancelar confirmação | `dialog.dismiss()` → nenhuma request POST enviada |
| UC-05b | Executar da página de detalhe | Navegar para `/processos/{id}` → botão "Executar Agora" com mesmo fluxo |

---

### UC-06 — Deletar processo

**Ator:** Usuário do Toninho
**Pré-condição:** Processo existente.

**Fluxo principal:**
1. Criar processo via `create_processo`.
2. Navegar para `/processos`.
3. Localizar a row do processo na tabela.
4. Clicar no botão "Deletar" (ícone lixeira).
5. Aceitar diálogo: `"Deletar o processo 'X'? Esta ação não pode ser desfeita."`.
6. Interceptar request `DELETE /api/v1/processos/{id}`.
7. Verificar que a row desaparece da tabela (animação de `swap:0.5s`).
8. Recarregar a página e verificar que o processo **não** aparece mais.

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos

```
tests/e2e/
├── conftest.py                          ← UTILIZAR: fixtures create_processo, create_processo_com_config do PRD-020
├── test_uc04_busca_processos.py         ← CRIAR: testes UC-04 + variações
├── test_uc05_executar_processo.py       ← CRIAR: testes UC-05 + variações
└── test_uc06_deletar_processo.py        ← CRIAR: testes UC-06
```

### 4.2. Seletores de Elementos

| Elemento | Seletor Playwright |
|---|---|
| Campo de busca | `page.locator("input[name='search']")` |
| Dropdown status | `page.locator("select[name='status']")` |
| Tabela container | `page.locator("#processos-table")` |
| Indicador loading | `page.locator("#search-indicator")` |
| Row de processo | `page.locator(f"#processo-row-{processo_id}")` |
| Botão executar | `page.locator(f"#processo-row-{processo_id} button[title='Executar agora']")` |
| Botão deletar | `page.locator(f"#processo-row-{processo_id} button[title='Deletar']")` |
| Link ver detalhes | `page.locator(f"#processo-row-{processo_id} a:has-text('Ver detalhes')")` |

### 4.3. Tratamento do hx-confirm (Diálogos Nativos)

O `hx-confirm` dispara `window.confirm()`, que o Playwright intercepta como `dialog` event:

```python
def test_executar_com_confirmacao(self, page: Page) -> None:
    """Aceitar diálogo de confirmação dispara POST."""
    page.goto("/processos")

    # Configurar handler para aceitar o diálogo
    page.on("dialog", lambda dialog: dialog.accept())

    # Interceptar a request POST
    with page.expect_response("**/api/v1/processos/*/execucoes") as resp_info:
        page.locator("button[title='Executar agora']").first.click()

    assert resp_info.value.status == 201


def test_cancelar_confirmacao_nao_faz_request(self, page: Page) -> None:
    """Cancelar diálogo de confirmação não dispara request."""
    page.goto("/processos")

    requests_made = []
    page.on("request", lambda req: requests_made.append(req.url))

    # Configurar handler para rejeitar o diálogo
    page.on("dialog", lambda dialog: dialog.dismiss())

    page.locator("button[title='Executar agora']").first.click()

    # Nenhuma request POST para execucoes
    post_requests = [r for r in requests_made if "execucoes" in r]
    assert len(post_requests) == 0
```

### 4.4. Aguardando Debounce HTMX

O debounce de 500ms exige que o teste aguarde a resposta HTMX:

```python
def test_busca_com_debounce(self, page: Page) -> None:
    """Busca HTMX dispara após 500ms de debounce."""
    page.goto("/processos")

    # Interceptar a request de busca
    with page.expect_response("**/processos/search*") as resp_info:
        page.locator("input[name='search']").fill("Alpha")

    # Response deve ter chegado (auto-aguardado pelo expect_response)
    assert resp_info.value.status == 200

    # Validar que apenas "Alpha" está visível
    expect(page.locator("#processos-table")).to_contain_text("Alpha")
    expect(page.locator("#processos-table")).not_to_contain_text("Beta")
```

### 4.5. Verificando Remoção Animada (UC-06)

O `hx-swap="outerHTML swap:0.5s"` remove a row com animação:

```python
def test_deletar_remove_row(self, page: Page) -> None:
    """Deletar processo remove a row da tabela com animação."""
    page.goto("/processos")

    row = page.locator(f"#processo-row-{processo_id}")
    expect(row).to_be_visible()

    # Aceitar diálogo de confirmação
    page.on("dialog", lambda dialog: dialog.accept())

    with page.expect_response(f"**/api/v1/processos/{processo_id}") as resp_info:
        row.locator("button[title='Deletar']").click()

    assert resp_info.value.status == 200

    # Row deve desaparecer (Playwright aguarda automaticamente)
    expect(row).not_to_be_visible()
```

---

## 5. Dependências

### 5.1. PRDs Anteriores

| PRD | Dependência |
|---|---|
| PRD-019 | **Obrigatório** — infraestrutura, live_server, Makefile |
| PRD-020 | **Obrigatório** — fixtures `create_processo`, `create_processo_com_config` |
| PRD-015 | Interface CRUD Processos — templates sob teste |

### 5.2. Endpoints da API Utilizados

| Método | Endpoint | Uso |
|---|---|---|
| POST | `/api/v1/processos` | Seeding de processos para busca/filtro |
| POST | `/api/v1/processos/{id}/configuracoes` | Seeding de configuração (pré-requisito para executar) |
| GET | `/processos/search` | Endpoint HTMX de busca (testado indiretamente) |
| POST | `/api/v1/processos/{id}/execucoes` | Executar processo (interceptado) |
| DELETE | `/api/v1/processos/{id}` | Deletar processo (interceptado) |

---

## 6. Regras de Negócio

### 6.1. Debounce de Busca

- O HTMX usa `delay:500ms` — a request só é disparada 500ms após a última tecla.
- Se o usuário continuar digitando dentro dos 500ms, o timer reinicia.
- O Playwright lida com isso automaticamente via `expect_response`.

### 6.2. hx-include para Parâmetros Combinados

- O campo de busca usa `hx-include="[name='status']"` — envia o valor do dropdown junto.
- O dropdown usa `hx-include="[name='search']"` — envia o valor do campo de busca junto.
- Isso garante que busca + filtro funcionam em conjunto.

### 6.3. Confirmação Antes de Ações Destrutivas

- `hx-confirm` exibe `window.confirm()` nativo do browser.
- Se o usuário cancela, nenhuma request é feita.
- O texto da confirmação é personalizado por ação:
  - Executar: `"Executar processo '{nome}' agora?"`
  - Deletar: `"Deletar o processo '{nome}'? Esta ação não pode ser desfeita."`

### 6.4. hx-swap="none" vs "outerHTML"

- **Executar** usa `hx-swap="none"` — o DOM da tabela não é alterado pela response direta. A atualização ocorre via polling ou navegação.
- **Deletar** usa `hx-swap="outerHTML swap:0.5s"` — a row é removida do DOM com animação CSS de 0.5s.

---

## 7. Casos de Teste

### 7.1. UC-04 — Busca e Filtro

- ✅ Digitar nome no campo de busca → tabela atualiza após debounce com resultados filtrados
- ✅ Selecionar status no dropdown → tabela atualiza imediatamente (`hx-trigger="change"`)
- ✅ Busca + filtro combinados → `hx-include` envia ambos os parâmetros
- ✅ Busca sem resultados → tabela exibe mensagem de estado vazio
- ✅ Limpar busca → tabela volta a exibir todos os processos
- ✅ Request HTMX vai para `/processos/search` (não recarrega a página)
- ✅ `#processos-table` recebe o conteúdo atualizado (`hx-swap="innerHTML"`)

### 7.2. UC-05 — Executar Processo

- ✅ Clicar executar → diálogo de confirmação aparece com nome do processo
- ✅ Aceitar confirmação → POST `/api/v1/processos/{id}/execucoes` retorna 201
- ✅ Cancelar confirmação → nenhuma request feita
- ✅ Executar da página de detalhe → mesmo comportamento

### 7.3. UC-06 — Deletar Processo

- ✅ Clicar deletar → diálogo de confirmação com aviso irreversível
- ✅ Aceitar confirmação → DELETE retorna 200
- ✅ Row desaparece da tabela após delete (animação)
- ✅ Recarregar página → processo não aparece mais

---

## 8. Critérios de Aceite

- [ ] Busca HTMX filtra processos por nome com debounce de 500ms.
- [ ] Filtro por status atualiza tabela sem recarregar página.
- [ ] Busca + filtro combinados funcionam via `hx-include`.
- [ ] Executar processo exibe confirmação e faz POST após aceitar.
- [ ] Cancelar confirmação não dispara request.
- [ ] Deletar processo remove row com animação e processo não reaparece.
- [ ] Todos os testes passam com `make test-e2e`.

---

## 9. Notas e Observações

### 9.1. Seeding de Dados para Busca

UC-04 precisa de múltiplos processos. Usar nomes únicos e previsíveis para facilitar assertivas:

```python
@pytest.fixture
def processos_para_busca(create_processo):
    """Cria 3 processos com nomes distintos para testes de busca."""
    return [
        create_processo(nome="Alpha E2E Busca", status="ativo"),
        create_processo(nome="Beta E2E Busca", status="inativo"),
        create_processo(nome="Gamma E2E Busca", status="ativo"),
    ]
```

### 9.2. Seletores de Row

Os IDs das rows (`#processo-row-{id}`) usam o UUID do processo. O ID é obtido em tempo de teste via fixture de seeding, não hardcoded.

### 9.3. Paginação

Se houver muitos processos no banco (de testes anteriores), a tabela pode paginar. Os testes devem usar nomes suficientemente únicos para que a busca encontre o processo correto independente da paginação.
