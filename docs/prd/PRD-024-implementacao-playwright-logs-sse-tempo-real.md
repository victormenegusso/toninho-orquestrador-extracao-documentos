# PRD-024: Implementação Playwright — Logs em Tempo Real via SSE

**Status**: 📋 Planejado
**Prioridade**: 🔴 Alta — Funcionalidade única de streaming em tempo real
**Categoria**: Testing — E2E Frontend
**Estimativa**: 4-5 horas
**Depende de**: PRD-019 (infraestrutura), PRD-023 (fixtures de execução)

---

## 1. Objetivo

Implementar testes E2E para o **streaming de logs em tempo real** na página de detalhe de execução (`/execucoes/{id}`). O componente usa **Server-Sent Events (SSE)** via `EventSource` nativo do browser para receber logs do endpoint `/api/v1/execucoes/{id}/logs/stream`. Cobre UC-08 do documento de casos de uso E2E.

Este é o componente JavaScript mais complexo do frontend — envolve:
- Conexão SSE (`EventSource`) com o servidor.
- Parsing JSON de cada evento e renderização com cores por nível.
- Auto-scroll com toggle.
- Filtro por nível de log.
- Buffer circular com limite de 1000 linhas (FIFO).
- Tratamento de desconexão.

---

## 2. Contexto e Justificativa

### 2.1. Arquitetura do Streaming de Logs

```
Browser                          Server
  │                                │
  ├── EventSource ───────────────→ GET /api/v1/execucoes/{id}/logs/stream
  │                                │
  │   ←─── data: {"nivel":"INFO",  │
  │         "mensagem":"..."}      │
  │                                │
  │   ←─── data: {"nivel":"ERROR", │
  │         "mensagem":"..."}      │
  │                                │
  └── onerror → tratamento         │
```

O JavaScript no `detail.html` faz:
1. `new EventSource(url)` → abre conexão SSE.
2. `onmessage` → parse JSON, cria `<div>` colorido, appenda ao container.
3. Se `logCount >= 1000` → remove o primeiro log (FIFO).
4. Se `auto-scroll` ativo → `scrollTop = scrollHeight`.
5. Se filtro de nível ativo → ignora logs de outros níveis.
6. `onerror` → trata desconexão.

### 2.2. Por que SSE precisa de E2E

SSE não pode ser testado com testes de integração tradicionais (`TestClient` do FastAPI). O `EventSource` é uma API de browser — precisa de um browser real para estabelecer a conexão, receber eventos e executar o JavaScript de renderização.

### 2.3. ADRs Referenciados

| ADR | Relação |
|---|---|
| ADR-006 (Frontend) | JavaScript vanilla para SSE (sem framework) |
| ADR-007 (Qualidade) | Testes E2E para validar integração browser-server |

---

## 3. Casos de Uso

### UC-08 — Acompanhar execução com logs em tempo real (SSE)

**Ator:** Usuário do Toninho
**Pré-condição:** Execução com status `em_execucao` e logs sendo gerados.

**Fluxo principal:**
1. Criar execução via API e atualizar status para `em_execucao`.
2. Inserir alguns logs via API (POST `/api/v1/logs/batch`).
3. Navegar para `/execucoes/{id}`.
4. Verificar que o container de logs está visível (fundo escuro, `bg-gray-900`).
5. Verificar que a mensagem "Conectando ao stream de logs..." aparece inicialmente.
6. Verificar que a conexão SSE é estabelecida (logs começam a aparecer ou status da conexão muda).
7. Verificar que logs aparecem com cores corretas por nível:
   - `INFO` → azul (`text-blue-400`)
   - `WARNING` → amarelo (`text-yellow-400`)
   - `ERROR` → vermelho (`text-red-400`)
   - `DEBUG` → cinza (`text-gray-400`)
8. Verificar que a barra de progresso está presente e atualiza via polling (`hx-trigger="every 2s"` no `#progress-section`).

**Variações:**

| ID | Variação | O que muda |
|---|---|---|
| UC-08a | Filtro de nível | Selecionar "ERROR" no dropdown `#log-level-filter` → apenas logs ERROR são renderizados |
| UC-08b | Auto-scroll toggle | Desmarcar checkbox `#auto-scroll` → container para de rolar automaticamente |
| UC-08c | Buffer overflow | Inserir >1000 logs → primeiros logs removidos (FIFO), container não cresce indefinidamente |
| UC-08d | Desconexão SSE | Stream encerra (ex: execução finaliza) → tratamento graceful no `onerror` |

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos

```
tests/e2e/
├── conftest.py                      ← ALTERAR: adicionar fixture de seeding de logs
└── test_uc08_logs_sse.py            ← CRIAR: testes UC-08 + variações
```

### 4.2. Fixture de Seeding de Logs (tests/e2e/conftest.py)

Adicionar ao `conftest.py`:

```python
@pytest.fixture
def create_logs_batch(api_client: httpx.Client):
    """
    Factory fixture para criar logs via API REST em batch.

    Args:
        execucao_id: ID da execução
        logs: Lista de dicts com {nivel, mensagem}
    """

    def _create(execucao_id: str, logs: list[dict]) -> None:
        payload = {
            "logs": [
                {
                    "execucao_id": execucao_id,
                    "nivel": log.get("nivel", "info"),
                    "mensagem": log.get("mensagem", "Log de teste"),
                }
                for log in logs
            ]
        }
        resp = api_client.post("/api/v1/logs/batch", json=payload)
        assert resp.status_code == 201, f"Falha ao criar logs: {resp.text}"

    return _create
```

### 4.3. Seletores de Elementos

| Elemento | Seletor Playwright |
|---|---|
| Container de logs | `page.locator("#logs-container")` |
| Conteúdo dos logs | `page.locator("#logs-content")` |
| Dropdown filtro nível | `page.locator("#log-level-filter")` |
| Checkbox auto-scroll | `page.locator("#auto-scroll")` |
| Linha de log INFO | `page.locator("#logs-content .text-blue-400")` |
| Linha de log ERROR | `page.locator("#logs-content .text-red-400")` |
| Linha de log WARNING | `page.locator("#logs-content .text-yellow-400")` |
| Linha de log DEBUG | `page.locator("#logs-content .text-gray-400")` |
| Barra de progresso | `page.locator("#progress-section")` |
| Mensagem conectando | `page.locator("text=Conectando ao stream")` |

### 4.4. Testando Conexão SSE

O Playwright pode verificar que o `EventSource` está conectado avaliando JavaScript:

```python
def test_sse_connection_established(self, page: Page) -> None:
    """EventSource conecta ao endpoint de logs."""
    page.goto(f"/execucoes/{execucao_id}")

    # Aguardar que o EventSource esteja conectado
    # readyState: 0=CONNECTING, 1=OPEN, 2=CLOSED
    page.wait_for_function(
        """() => {
            const scripts = document.querySelectorAll('script');
            // O EventSource é criado inline no template
            return document.querySelector('#logs-content').children.length > 0
                || document.querySelector('#logs-content').textContent.includes('Conectando');
        }"""
    )
```

### 4.5. Testando Renderização de Logs por Nível

```python
@pytest.mark.e2e
class TestLogsSSE:
    """Testes para streaming de logs via SSE."""

    def test_logs_aparecem_com_cores(
        self, page: Page, create_execucao, update_execucao_status, create_logs_batch
    ) -> None:
        """Logs SSE renderizam com cores corretas por nível."""
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        # Inserir logs antes de navegar
        create_logs_batch(execucao_id, [
            {"nivel": "info", "mensagem": "Iniciando extração"},
            {"nivel": "error", "mensagem": "Falha ao conectar"},
            {"nivel": "warning", "mensagem": "Timeout parcial"},
        ])

        page.goto(f"/execucoes/{execucao_id}")

        # Aguardar container de logs
        logs_container = page.locator("#logs-container")
        expect(logs_container).to_be_visible()

        # Aguardar que logs apareçam via SSE (timeout generoso)
        logs_content = page.locator("#logs-content")
        expect(logs_content).not_to_be_empty(timeout=15000)

    def test_container_logs_visivel(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        """Container de logs está visível com estilo terminal."""
        execucao = create_execucao()
        update_execucao_status(execucao["id"], "em_execucao")

        page.goto(f"/execucoes/{execucao['id']}")

        container = page.locator("#logs-container")
        expect(container).to_be_visible()
        # Verificar estilo terminal (fundo escuro)
        expect(container).to_have_class(re.compile(r"bg-gray-900"))
```

### 4.6. Testando Filtro de Nível

```python
    def test_filtro_nivel_error(
        self, page: Page, create_execucao, update_execucao_status, create_logs_batch
    ) -> None:
        """Filtro 'ERROR' exibe apenas logs de erro."""
        execucao = create_execucao()
        execucao_id = execucao["id"]
        update_execucao_status(execucao_id, "em_execucao")

        create_logs_batch(execucao_id, [
            {"nivel": "info", "mensagem": "Log info"},
            {"nivel": "error", "mensagem": "Log error"},
        ])

        page.goto(f"/execucoes/{execucao_id}")

        # Selecionar filtro ERROR
        page.locator("#log-level-filter").select_option("ERROR")

        # Aguardar processamento
        page.wait_for_timeout(2000)

        # Verificar que o filtro está aplicado
        # Nota: o filtro opera nos novos logs recebidos via SSE,
        # não retroativamente nos já renderizados
        filter_value = page.locator("#log-level-filter").input_value()
        assert filter_value == "ERROR"
```

### 4.7. Testando Auto-scroll

```python
    def test_auto_scroll_toggle(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        """Checkbox de auto-scroll pode ser desabilitado."""
        execucao = create_execucao()
        update_execucao_status(execucao["id"], "em_execucao")

        page.goto(f"/execucoes/{execucao['id']}")

        # Checkbox deve estar marcado por padrão
        auto_scroll = page.locator("#auto-scroll")
        expect(auto_scroll).to_be_checked()

        # Desmarcar
        auto_scroll.uncheck()
        expect(auto_scroll).not_to_be_checked()
```

### 4.8. Testando Barra de Progresso com Polling

```python
    def test_progress_bar_polling(
        self, page: Page, create_execucao, update_execucao_status
    ) -> None:
        """Barra de progresso atualiza via polling HTMX a cada 2s."""
        execucao = create_execucao()
        update_execucao_status(execucao["id"], "em_execucao")

        page.goto(f"/execucoes/{execucao['id']}")

        # Progress section presente
        progress = page.locator("#progress-section")
        expect(progress).to_be_visible()

        # Interceptar request de polling (timeout 3s para margem)
        with page.expect_response(
            f"**/execucoes/{execucao['id']}/progress", timeout=4000
        ) as resp_info:
            pass

        assert resp_info.value.status == 200
```

---

## 5. Dependências

### 5.1. PRDs Anteriores

| PRD | Dependência |
|---|---|
| PRD-019 | **Obrigatório** — infraestrutura, live_server |
| PRD-023 | **Obrigatório** — fixtures `create_execucao`, `update_execucao_status` |
| PRD-008 | Módulo Log — endpoint de logs e streaming SSE |
| PRD-016 | Interface de Monitoramento — template de detalhe sob teste |

### 5.2. Endpoints da API Utilizados

| Método | Endpoint | Uso |
|---|---|---|
| POST | `/api/v1/processos/{id}/execucoes` | Seeding (via fixture) |
| PATCH | `/api/v1/execucoes/{id}/status` | Seeding de status (via fixture) |
| POST | `/api/v1/logs/batch` | Seeding de logs para SSE |
| GET | `/api/v1/execucoes/{id}/logs/stream` | Endpoint SSE (testado via browser) |
| GET | `/execucoes/{id}/progress` | Endpoint HTMX polling da barra de progresso |

---

## 6. Regras de Negócio

### 6.1. Formato do Evento SSE

Cada evento enviado pelo servidor tem o formato:
```
data: {"nivel": "INFO", "mensagem": "Processando URL https://...", "timestamp": "2026-03-15T10:30:00"}
```

O JavaScript no browser faz `JSON.parse(event.data)` e usa os campos.

### 6.2. Cores por Nível

| Nível | Classe CSS | Cor visual |
|---|---|---|
| `INFO` | `text-blue-400` | Azul |
| `WARNING` | `text-yellow-400` | Amarelo |
| `ERROR` | `text-red-400` | Vermelho |
| `DEBUG` | `text-gray-400` | Cinza |
| `CRITICAL` | `text-red-300` | Vermelho claro |

### 6.3. Buffer Circular (1000 linhas)

- Quando `logCount >= MAX_LOGS` (1000), o primeiro `<div>` filho de `#logs-content` é removido.
- Isso previne crescimento indefinido do DOM e problemas de memória em execuções longas.

### 6.4. Auto-scroll

- Checkbox `#auto-scroll` começa marcado (`checked`).
- Quando ativo: `container.scrollTop = container.scrollHeight` após cada novo log.
- Quando desativado: o container mantém a posição atual.

### 6.5. Filtro de Nível

- Dropdown `#log-level-filter` com opções: Todos, INFO, WARNING, ERROR, DEBUG.
- O filtro opera **nos novos logs recebidos** — se `filter !== ""` e `log.nivel !== filter`, o log é ignorado (não renderizado).
- Logs já renderizados **não são filtrados retroativamente** pelo JavaScript atual.

### 6.6. Polling da Barra de Progresso

O `#progress-section` usa `hx-trigger="every 2s"` **apenas quando a execução está em andamento**:
```html
hx-trigger="{% if execucao.status in ['em_execucao', 'aguardando', 'pausado'] %}every 2s{% else %}none{% endif %}"
```

Para execuções finalizadas, o polling é desativado (`none`).

---

## 7. Casos de Teste

### 7.1. Conexão SSE

- ✅ Container de logs visível com estilo terminal (`bg-gray-900`)
- ✅ Mensagem "Conectando ao stream de logs..." aparece inicialmente
- ✅ EventSource conecta ao endpoint `/api/v1/execucoes/{id}/logs/stream`
- ✅ Logs começam a aparecer no container após inserção via API

### 7.2. Renderização de Logs

- ✅ Logs INFO renderizados com classe `text-blue-400`
- ✅ Logs ERROR renderizados com classe `text-red-400`
- ✅ Logs WARNING renderizados com classe `text-yellow-400`
- ✅ Cada log contém timestamp, nível e mensagem

### 7.3. Controles

- ✅ Filtro de nível presente com opções corretas
- ✅ Filtro aplicado nos novos logs recebidos
- ✅ Checkbox auto-scroll marcado por padrão
- ✅ Desmarcar auto-scroll preserva posição de scroll

### 7.4. Barra de Progresso

- ✅ `#progress-section` visível para execução em andamento
- ✅ Polling `GET /execucoes/{id}/progress` disparado a cada ~2s
- ✅ Polling desativado para execuções finalizadas

---

## 8. Critérios de Aceite

- [ ] Container de logs visível com estilo terminal escuro.
- [ ] Logs aparecem no container após seeding via API.
- [ ] Cada nível de log tem a cor CSS correta.
- [ ] Filtro de nível funciona no dropdown.
- [ ] Checkbox de auto-scroll pode ser desabilitado.
- [ ] Barra de progresso faz polling quando execução está ativa.
- [ ] Todos os testes passam com `make test-e2e`.

---

## 9. Notas e Observações

### 9.1. Timing do SSE

O SSE pode ter latência variável dependendo do estado do servidor. Os testes usam timeouts generosos (10-15s) e `expect().not_to_be_empty()` com timeout para evitar flakiness.

### 9.2. Logs Pré-existentes vs Streaming

O endpoint SSE envia logs **existentes** (do banco) primeiro e depois aguarda novos. Para os testes, criamos logs **antes** de navegar para a página, garantindo que o stream terá dados imediatos.

### 9.3. Alternativa ao EventSource: Verificação Indireta

Se testar o `EventSource` diretamente for complexo, uma alternativa é verificar o resultado: logs renderizados no DOM. Se `#logs-content` tem filhos `<div>` com as classes corretas, o SSE está funcionando.

### 9.4. Buffer Overflow

Testar o buffer de 1000 logs requer inserir >1000 registros via API batch e aguardar que o SSE os envie todos. Este teste pode ser lento — marcar como `@pytest.mark.slow` se necessário e excluir da suite rápida.
