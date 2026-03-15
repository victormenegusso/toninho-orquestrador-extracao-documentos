# PRD-022: Implementação Playwright — Dashboard com Polling Automático

**Status**: 📋 Planejado
**Prioridade**: 🔴 Alta — Fluxo principal de monitoramento
**Categoria**: Testing — E2E Frontend
**Estimativa**: 3-4 horas
**Depende de**: PRD-019 (infraestrutura)

---

## 1. Objetivo

Implementar testes E2E para o **dashboard** (`/dashboard`) que utiliza **dois mecanismos de polling HTMX independentes**: cards de estatísticas atualizando a cada 5s e execuções ativas atualizando a cada 3s. Cobre UC-07 do documento de casos de uso E2E.

O dashboard é a página de entrada do sistema após o login e é o principal ponto de monitoramento operacional. Testar o polling garante que os dados se mantêm atualizados sem intervenção do usuário.

---

## 2. Contexto e Justificativa

### 2.1. Mecanismos de Polling no Dashboard

O dashboard possui dois componentes HTMX com polling automático:

| Componente | Trigger | Endpoint | Target | Swap |
|---|---|---|---|---|
| Cards de estatísticas | `hx-trigger="every 5s"` | `GET /dashboard/stats` | `#stats-cards` | `outerHTML` |
| Execuções ativas | `hx-trigger="every 3s"` | `GET /execucoes/ativas` | `#execucoes-ativas` | `innerHTML` |

Ambos funcionam de forma **independente** — cada um faz suas requests no seu próprio intervalo.

### 2.2. ADRs Referenciados

| ADR | Relação |
|---|---|
| ADR-006 (Frontend) | HTMX polling como alternativa a WebSockets para atualização em tempo real |
| ADR-007 (Qualidade) | Testes de comportamento reativo |

---

## 3. Casos de Uso

### UC-07 — Dashboard com polling automático

**Ator:** Usuário do Toninho
**Pré-condição:** Servidor rodando.

**Fluxo principal:**
1. Navegar para `/dashboard`.
2. Verificar que os **4 cards de estatísticas** estão visíveis:
   - Total de Execuções (borda azul)
   - Execuções Ativas (borda amarela)
   - Concluídas (borda verde)
   - Taxa de Sucesso (borda roxa)
3. Verificar que a seção de **execuções ativas** está visível (pode estar vazia ou com cards).
4. Verificar que os **quick actions** (botões de atalho) estão presentes:
   - "Novo Processo" → link para `/processos/novo`
   - "Ver Processos" → link para `/processos`
   - "Ver Execuções" → link para `/execucoes`
   - "API Docs" → link para `/docs`
5. Aguardar **~5s** e interceptar a request `GET /dashboard/stats`.
6. Verificar que os cards de estatísticas foram atualizados (swap `outerHTML` no `#stats-cards`).
7. Aguardar **~3s** e interceptar a request `GET /execucoes/ativas`.
8. Verificar que a seção de execuções ativas foi atualizada (swap `innerHTML` no `#execucoes-ativas`).

**Pós-condição:** Dashboard exibe dados atualizados sem reload manual.

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos

```
tests/e2e/
├── conftest.py                          ← UTILIZAR: fixtures existentes
└── test_uc07_dashboard_polling.py       ← CRIAR: testes UC-07
```

### 4.2. Seletores de Elementos

| Elemento | Seletor Playwright |
|---|---|
| Container stats | `page.locator("#stats-cards")` |
| Card Total Execuções | `page.locator("#stats-cards .border-blue-500")` |
| Card Execuções Ativas | `page.locator("#stats-cards .border-yellow-500")` |
| Card Concluídas | `page.locator("#stats-cards .border-green-500")` |
| Card Taxa de Sucesso | `page.locator("#stats-cards .border-purple-500")` |
| Container exec. ativas | `page.locator("#execucoes-ativas")` |
| Link Novo Processo | `page.locator("a[href='/processos/novo']")` |
| Link Ver Processos | `page.locator("a[href='/processos']")` |
| Link Ver Execuções | `page.locator("a[href='/execucoes']")` |

### 4.3. Testando Polling HTMX

Para verificar que o polling está funcionando, interceptar requests HTTP no intervalo esperado:

```python
@pytest.mark.e2e
class TestDashboardPolling:
    """Testes para polling automático do dashboard."""

    def test_stats_polling_every_5s(self, page: Page) -> None:
        """Cards de estatísticas atualizam via polling a cada 5s."""
        page.goto("/dashboard")

        # Verificar que os 4 cards estão presentes
        expect(page.locator("#stats-cards")).to_be_visible()

        # Aguardar a primeira request de polling (até 6s para ter margem)
        with page.expect_response(
            "**/dashboard/stats", timeout=7000
        ) as resp_info:
            pass  # Apenas aguarda — o polling é automático

        assert resp_info.value.status == 200

    def test_execucoes_ativas_polling_every_3s(self, page: Page) -> None:
        """Seção de execuções ativas atualiza via polling a cada 3s."""
        page.goto("/dashboard")

        expect(page.locator("#execucoes-ativas")).to_be_visible()

        # Aguardar a primeira request de polling (até 4s para ter margem)
        with page.expect_response(
            "**/execucoes/ativas", timeout=5000
        ) as resp_info:
            pass  # Polling automático

        assert resp_info.value.status == 200

    def test_stats_update_after_creating_processo(
        self, page: Page, create_processo
    ) -> None:
        """Stats refletem novo processo após polling."""
        page.goto("/dashboard")

        # Capturar valor atual de Total de Execuções
        stats_card = page.locator("#stats-cards")
        expect(stats_card).to_be_visible()

        # Criar processo via API (em background)
        create_processo(nome="Dashboard Poll Test")

        # Aguardar próximo ciclo de polling (até 6s)
        with page.expect_response("**/dashboard/stats", timeout=7000):
            pass

        # Stats foram atualizadas (o importante é que o polling funcionou)
        expect(stats_card).to_be_visible()
```

### 4.4. Testando Quick Actions

```python
    def test_quick_action_novo_processo(self, page: Page) -> None:
        """Botão 'Novo Processo' leva para /processos/novo."""
        page.goto("/dashboard")

        page.locator("a[href='/processos/novo']").click()
        page.wait_for_url("**/processos/novo")
        expect(page).to_have_url("**/processos/novo")

    def test_quick_action_ver_processos(self, page: Page) -> None:
        """Botão 'Ver Processos' leva para /processos."""
        page.goto("/dashboard")

        page.locator("a[href='/processos']").click()
        page.wait_for_url("**/processos")
```

### 4.5. Verificando Conteúdo dos Cards

```python
    def test_cards_exibem_numeros(self, page: Page) -> None:
        """Cada card exibe um valor numérico."""
        page.goto("/dashboard")

        # Card de Total deve ter um número
        total_card = page.locator("#stats-cards .border-blue-500")
        expect(total_card).to_be_visible()
        # O valor é um <p class="text-2xl font-bold">
        total_value = total_card.locator("p.text-2xl")
        expect(total_value).to_be_visible()
        # Deve conter um número (0, 1, 2, etc.)
        expect(total_value).to_have_text(re.compile(r"\d+"))

    def test_taxa_sucesso_exibe_percentual(self, page: Page) -> None:
        """Card de taxa de sucesso exibe valor com %."""
        page.goto("/dashboard")

        taxa_card = page.locator("#stats-cards .border-purple-500")
        taxa_value = taxa_card.locator("p.text-2xl")
        expect(taxa_value).to_have_text(re.compile(r"\d+\.?\d*%"))
```

---

## 5. Dependências

### 5.1. PRDs Anteriores

| PRD | Dependência |
|---|---|
| PRD-019 | **Obrigatório** — infraestrutura, live_server, Makefile |
| PRD-016 | Interface de Monitoramento — template dashboard sob teste |

### 5.2. Endpoints Envolvidos

| Método | Endpoint | Uso |
|---|---|---|
| GET | `/dashboard` | Página principal (navegação) |
| GET | `/dashboard/stats` | Partial HTMX com cards de estatísticas (polling 5s) |
| GET | `/execucoes/ativas` | Partial HTMX com execuções em andamento (polling 3s) |

---

## 6. Regras de Negócio

### 6.1. Polling Independente

- Os dois pollings são independentes — se um falhar, o outro continua.
- O HTMX gerencia os timers automaticamente — não há JavaScript custom.
- `hx-trigger="every 5s"` dispara ~5s após a última resposta (não após a última request).

### 6.2. Cards de Estatísticas

O partial `partials/dashboard_stats.html` retorna 4 cards com:
- **Total de Execuções**: `metrics.executions.total`
- **Execuções Ativas**: `metrics.executions.active`
- **Concluídas**: `metrics.executions.completed`
- **Taxa de Sucesso**: `metrics.success_rate` (percentual com 1 casa decimal)

O swap é `outerHTML` — o `#stats-cards` inteiro é substituído (incluindo o elemento container).

### 6.3. Execuções Ativas

O partial `partials/execucoes_ativas.html` retorna cards individuais para cada execução com status `em_execucao`, `aguardando` ou `pausado`. Se não houver execuções ativas, exibe mensagem informativa.

O swap é `innerHTML` — apenas o conteúdo interno do `#execucoes-ativas` é substituído.

### 6.4. Quick Actions

Os links de atalho usam `hx-boost="true"` (herdado do `<body>`) — a navegação é feita via HTMX sem full page reload.

---

## 7. Casos de Teste

### 7.1. Estrutura do Dashboard

- ✅ Dashboard carrega com 4 cards de estatísticas visíveis
- ✅ Cada card tem label (text-gray-600) e valor numérico (text-2xl font-bold)
- ✅ Cards têm cores de borda corretas: azul, amarelo, verde, roxo
- ✅ Seção de execuções ativas está presente
- ✅ Quick actions (4 botões de atalho) estão presentes e funcionais

### 7.2. Polling de Estatísticas (5s)

- ✅ Request `GET /dashboard/stats` é disparada automaticamente dentro de ~5s
- ✅ Response substitui o container `#stats-cards` via outerHTML
- ✅ Valores numéricos nos cards são atualizados
- ✅ Polling continua após múltiplos ciclos

### 7.3. Polling de Execuções Ativas (3s)

- ✅ Request `GET /execucoes/ativas` é disparada automaticamente dentro de ~3s
- ✅ Response atualiza o conteúdo de `#execucoes-ativas`
- ✅ Se não há execuções ativas, exibe mensagem apropriada

### 7.4. Quick Actions

- ✅ "Novo Processo" navega para `/processos/novo`
- ✅ "Ver Processos" navega para `/processos`
- ✅ "Ver Execuções" navega para `/execucoes`
- ✅ "API Docs" abre `/docs` (verificar que o link existe, sem navegar)

---

## 8. Critérios de Aceite

- [ ] Dashboard carrega com os 4 cards de estatísticas e valores numéricos.
- [ ] Polling de stats (5s) interceptado e responde com dados válidos.
- [ ] Polling de execuções ativas (3s) interceptado e funciona.
- [ ] Quick actions levam às páginas corretas.
- [ ] Todos os testes passam com `make test-e2e`.
- [ ] Testes toleram dados pré-existentes (não dependem de banco vazio).

---

## 9. Notas e Observações

### 9.1. Timeout nos Testes de Polling

Os testes de polling usam `timeout` generoso (7000ms para 5s, 5000ms para 3s) para evitar flakiness. O HTMX pode ter variação de ±500ms no intervalo real.

### 9.2. Sem Workers Celery

O dashboard funciona mesmo sem workers — ele exibe contadores e cards baseados nos dados do banco. Processos e execuções criados via API são suficientes para alimentar os cards.

### 9.3. Import de `re` para Regex

Os testes que validam formato numérico usam `import re` para `re.compile()` nas assertivas `to_have_text`.
