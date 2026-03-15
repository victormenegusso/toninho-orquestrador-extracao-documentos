# PRD-020: Implementação Playwright — CRUD de Processos

**Status**: 📋 Planejado
**Prioridade**: 🔴 Alta — Formulário Alpine.js é o componente mais complexo do frontend
**Categoria**: Testing — E2E Frontend
**Estimativa**: 4-6 horas
**Depende de**: PRD-019 (infraestrutura Playwright)

---

## 1. Objetivo

Implementar testes E2E para o **formulário de criação e edição de processos** — o componente Alpine.js mais complexo do frontend. Cobre os casos de uso UC-01 (criar processo), UC-02 (validação) e UC-03 (editar processo) do documento de casos de uso E2E.

O formulário é controlado pelo componente `processoForm()` em `frontend/templates/pages/processos/create.html` e envolve:
- Binding bidirecional Alpine.js (`x-model`) em 12+ campos.
- Campos condicionais (`x-show`) para agendamento e método de extração.
- Validação client-side com exibição inline de erros.
- Submissão assíncrona via `fetch()` em duas etapas (processo + configuração).

---

## 2. Contexto e Justificativa

### 2.1. Por que este componente é prioritário

O formulário de processos é o ponto de entrada principal do sistema. Um erro silencioso aqui (campo que não binds, validação que não aparece, submit que falha) impacta diretamente o fluxo de trabalho do usuário. O componente `processoForm()` tem:

- **12 campos** com `x-model` (text, number, textarea, select, checkbox).
- **3 campos condicionais** com `x-show` (cron, datetime, aviso Docling).
- **2 funções de validação** (`validateBasic()`, `validateConfig()`).
- **2 métodos de submissão** (`submit(false)` sem config, `submit(true)` com config).

Nenhum desses comportamentos é coberto pelos testes de integração existentes (que testam HTTP responses, não interações no browser).

### 2.2. ADRs Referenciados

| ADR | Relação |
|---|---|
| ADR-006 (Frontend) | Alpine.js para formulários reativos — comportamento sob teste |
| ADR-007 (Qualidade) | pytest + markers — estrutura dos testes |

---

## 3. Casos de Uso

### UC-01 — Criar processo com configuração completa

**Ator:** Usuário do Toninho
**Pré-condição:** Nenhum processo com nome duplicado.

**Fluxo principal:**
1. Navegar para `/processos/novo`.
2. Preencher campo **nome** (`x-model="form.nome"`): `"Processo E2E Teste"`.
3. Preencher campo **descrição** (`x-model="form.descricao"`): `"Descrição de teste"`.
4. Verificar que **status** está selecionado como `ativo` (default).
5. Na seção de configuração, preencher **URLs** (`x-model="config.urls"`): inserir 2 URLs (uma por linha).
6. Definir **timeout** (`x-model.number="config.timeout"`): `120`.
7. Definir **max_retries** (`x-model.number="config.max_retries"`): `2`.
8. Verificar **formato_saida** = `multiplos_arquivos` (default).
9. Verificar **metodo_extracao** = `html2text` (default).
10. Clicar no botão "Criar Processo" (`@click="submit(true)"`).
11. Aguardar redirecionamento para `/processos/{id}` (página de detalhe).
12. Verificar que o nome, descrição e configuração estão corretos na página de detalhe.

**Pós-condição:** Processo criado com configuração persistida no banco.

**Variações:**

| ID | Variação | O que muda no fluxo |
|---|---|---|
| UC-01a | Agendamento recorrente | Passo 5+: selecionar `agendamento_tipo = recorrente` → campo cron aparece (`x-show`) → preencher `"0 */6 * * *"` |
| UC-01b | Agendamento one_time | Passo 5+: selecionar `agendamento_tipo = one_time` → campo datetime aparece (`x-show`) → preencher data futura |
| UC-01c | Método Docling | Passo 5+: selecionar `metodo_extracao = docling` → aviso amarelo aparece (`x-show`) com texto sobre SPAs |
| UC-01d | Usar browser | Passo 5+: marcar checkbox `use_browser` → valor `true` enviado na configuração |

---

### UC-02 — Validação do formulário de processo

**Ator:** Usuário do Toninho
**Pré-condição:** Nenhuma.

**Fluxo principal (nome vazio):**
1. Navegar para `/processos/novo`.
2. Deixar campo **nome** vazio.
3. Clicar "Criar Processo".
4. Verificar que mensagem de erro aparece abaixo do campo nome.
5. Verificar que **nenhuma request HTTP** foi disparada (interceptar rede).
6. Verificar que a página **não recarregou**.

**Variações:**

| ID | Variação | Cenário | Validação esperada |
|---|---|---|---|
| UC-02a | Nome vazio | Campo nome em branco | Erro inline abaixo do campo nome |
| UC-02b | URLs vazias com config | Submit com config mas textarea URLs vazia | Erro inline abaixo do campo URLs |
| UC-02c | Timeout fora do range | Valor `0` ou `100000` | Erro inline no campo timeout |
| UC-02d | Cron inválido | `agendamento_tipo = recorrente` + cron `"abc"` | Erro inline no campo cron |
| UC-02e | Nome duplicado (servidor) | Nome já existente → API retorna 409 | `globalError` no topo do formulário |

---

### UC-03 — Editar processo existente

**Ator:** Usuário do Toninho
**Pré-condição:** Processo existe com configuração.

**Fluxo principal:**
1. Criar processo via `api_client` (fixture de seeding).
2. Navegar para `/processos/{id}/editar`.
3. Verificar que campo **nome** está pré-populado com o valor correto.
4. Verificar que campo **URLs** está pré-populado.
5. Verificar que campo **timeout** está pré-populado.
6. Alterar o **nome** para `"Processo Editado E2E"`.
7. Alterar o **timeout** para `300`.
8. Clicar "Salvar" (`@click="submit(true)"`).
9. Verificar redirecionamento para página de detalhe.
10. Verificar que os dados atualizados aparecem na página de detalhe.

**Pós-condição:** Processo atualizado via PUT (não POST).

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos

```
tests/e2e/
├── conftest.py                          ← ALTERAR: adicionar fixture de seeding de processos
├── test_uc01_criar_processo.py          ← CRIAR: testes UC-01 + variações
├── test_uc02_validacao_formulario.py    ← CRIAR: testes UC-02 + variações
└── test_uc03_editar_processo.py         ← CRIAR: testes UC-03
```

### 4.2. Fixture de Seeding (tests/e2e/conftest.py)

Adicionar ao `conftest.py` existente:

```python
@pytest.fixture
def create_processo(api_client: httpx.Client):
    """
    Factory fixture para criar processo via API REST.

    Retorna dict com os dados do processo criado.
    Aceita kwargs para customizar campos.
    """
    _counter = 0

    def _create(**kwargs) -> dict:
        nonlocal _counter
        _counter += 1
        payload = {
            "nome": kwargs.get("nome", f"Processo E2E {_counter}_{int(time.time())}"),
            "descricao": kwargs.get("descricao", "Processo criado para teste E2E"),
        }
        payload.update(kwargs)
        resp = api_client.post("/api/v1/processos", json=payload)
        assert resp.status_code == 201, f"Falha ao criar processo: {resp.text}"
        return resp.json()["data"]

    return _create


@pytest.fixture
def create_processo_com_config(api_client: httpx.Client, create_processo):
    """
    Factory fixture para criar processo + configuração via API REST.

    Retorna tuple (processo_data, config_data).
    """

    def _create(processo_kwargs=None, config_kwargs=None) -> tuple[dict, dict]:
        processo_kwargs = processo_kwargs or {}
        config_kwargs = config_kwargs or {}

        processo = create_processo(**processo_kwargs)
        processo_id = processo["id"]

        config_payload = {
            "urls": config_kwargs.get("urls", ["https://example.com"]),
            "timeout": config_kwargs.get("timeout", 3600),
            "max_retries": config_kwargs.get("max_retries", 3),
            "formato_saida": config_kwargs.get("formato_saida", "multiplos_arquivos"),
            "output_dir": config_kwargs.get("output_dir", "./output"),
            "agendamento_tipo": config_kwargs.get("agendamento_tipo", "manual"),
            "metodo_extracao": config_kwargs.get("metodo_extracao", "html2text"),
            "use_browser": config_kwargs.get("use_browser", False),
        }
        config_payload.update(config_kwargs)

        resp = api_client.post(
            f"/api/v1/processos/{processo_id}/configuracoes",
            json=config_payload,
        )
        assert resp.status_code == 201, f"Falha ao criar config: {resp.text}"
        config = resp.json()["data"]

        return processo, config

    return _create
```

### 4.3. Seletores de Elementos

Referência dos seletores para os campos do formulário (baseado em `create.html`):

| Campo | Seletor Playwright | Tipo |
|---|---|---|
| Nome | `page.locator("#nome")` | `<input type="text">` |
| Descrição | `page.locator("#descricao")` | `<textarea>` |
| Status | `page.locator("#status")` | `<select>` |
| URLs | `page.locator("#urls")` | `<textarea>` |
| Timeout | `page.locator("#timeout")` | `<input type="number">` |
| Max Retries | `page.locator("#max_retries")` | `<input type="number">` |
| Formato Saída | `page.locator("#formato_saida")` | `<select>` |
| Output Dir | `page.locator("#output_dir")` | `<input type="text">` |
| Agendamento Tipo | `page.locator("#agendamento_tipo")` | `<select>` |
| Agendamento Cron | `page.locator("#agendamento_cron")` | `<input type="text">` |
| Agendamento Datetime | `page.locator("#agendamento_datetime")` | `<input type="datetime-local">` |
| Método Extração | `page.locator("select[x-model='config.metodo_extracao']")` | `<select>` |
| Use Browser | `page.locator("input[x-model='config.use_browser']")` | `<input type="checkbox">` |
| Botão Criar/Salvar | `page.locator("button:has-text('Criar Processo')")` ou `page.locator("button:has-text('Salvar')")` | `<button>` |

### 4.4. Validação de Campos Condicionais

Os campos condicionais usam `x-show` do Alpine.js. Para testar:

```python
# Campo cron aparece quando agendamento_tipo = recorrente
page.locator("#agendamento_tipo").select_option("recorrente")
expect(page.locator("#agendamento_cron")).to_be_visible()

# Campo datetime aparece quando agendamento_tipo = one_time
page.locator("#agendamento_tipo").select_option("one_time")
expect(page.locator("#agendamento_datetime")).to_be_visible()

# Aviso Docling aparece quando metodo_extracao = docling
page.locator("select[x-model='config.metodo_extracao']").select_option("docling")
expect(page.locator("text=Atenção")).to_be_visible()
```

### 4.5. Interceptação de Requests

Para validar que o formulário faz as calls corretas:

```python
# Interceptar request de criação
with page.expect_response("**/api/v1/processos") as response_info:
    page.locator("button:has-text('Criar Processo')").click()

response = response_info.value
assert response.status == 201
data = response.json()["data"]
assert data["nome"] == "Processo E2E Teste"
```

Para validar que nenhuma request é feita em caso de erro de validação:

```python
# Monitorar requests
requests_made = []
page.on("request", lambda req: requests_made.append(req.url))

# Tentar submit com campo vazio
page.locator("button:has-text('Criar Processo')").click()

# Nenhuma request para a API
api_requests = [r for r in requests_made if "/api/v1/" in r]
assert len(api_requests) == 0
```

### 4.6. Exemplo de Teste Completo — UC-01

```python
"""Testes E2E — UC-01: Criar processo com configuração."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestCriarProcesso:
    """Testes para criação de processo via formulário Alpine.js."""

    def test_criar_processo_basico(self, page: Page) -> None:
        """Criar processo com configuração mínima."""
        page.goto("/processos/novo")

        # Preencher formulário
        page.locator("#nome").fill("Processo E2E Básico")
        page.locator("#descricao").fill("Teste de criação básica")

        # Preencher configuração
        page.locator("#urls").fill("https://example.com\nhttps://example.org")
        page.locator("#timeout").fill("120")
        page.locator("#max_retries").fill("2")

        # Submeter e aguardar response
        with page.expect_response("**/api/v1/processos") as resp_info:
            page.locator("button:has-text('Criar Processo')").click()

        assert resp_info.value.status == 201

        # Verificar redirecionamento para página de detalhe
        page.wait_for_url("**/processos/*")
        expect(page.locator("text=Processo E2E Básico")).to_be_visible()

    def test_campo_cron_aparece_agendamento_recorrente(self, page: Page) -> None:
        """Campo cron fica visível ao selecionar agendamento recorrente."""
        page.goto("/processos/novo")

        # Cron não deve estar visível inicialmente
        expect(page.locator("#agendamento_cron")).not_to_be_visible()

        # Selecionar agendamento recorrente
        page.locator("#agendamento_tipo").select_option("recorrente")

        # Cron agora deve estar visível
        expect(page.locator("#agendamento_cron")).to_be_visible()

    def test_aviso_docling_aparece(self, page: Page) -> None:
        """Aviso de limitação SPA aparece ao selecionar Docling."""
        page.goto("/processos/novo")

        # Selecionar Docling
        page.locator("select[x-model='config.metodo_extracao']").select_option("docling")

        # Aviso deve aparecer
        expect(page.locator("text=Atenção")).to_be_visible()
```

---

## 5. Dependências

### 5.1. PRDs Anteriores

| PRD | Dependência |
|---|---|
| PRD-019 | **Obrigatório** — infraestrutura, conftest.py, live_server, Makefile targets |
| PRD-015 | Interface CRUD Processos — templates e rotas sendo testadas |
| PRD-018 | Integração Docling — campo `metodo_extracao` no formulário |

### 5.2. Endpoints da API Utilizados (seeding)

| Método | Endpoint | Uso |
|---|---|---|
| POST | `/api/v1/processos` | Criar processo (seeding + validação de submit) |
| POST | `/api/v1/processos/{id}/configuracoes` | Criar configuração (seeding UC-03) |
| GET | `/api/v1/processos/{id}` | Validar dados após criação |

---

## 6. Regras de Negócio

### 6.1. Formulário processoForm()

- O componente Alpine.js `processoForm()` aceita `initialProcesso` e `initialConfig` como parâmetros.
- Na criação (`/processos/novo`), ambos são `null/undefined`.
- Na edição (`/processos/{id}/editar`), são populados com dados do servidor.
- O método `submit(withConfig)`:
  - Se `withConfig=false`: faz POST/PUT apenas do processo.
  - Se `withConfig=true`: faz POST/PUT do processo e depois upsert da configuração.

### 6.2. Validação Client-Side

- `validateBasic()` verifica: nome não vazio, status válido.
- `validateConfig()` verifica: URLs não vazias, timeout entre 1-86400, max_retries entre 0-10, cron válido (quando recorrente), datetime preenchido (quando one_time).
- Erros são armazenados em `errors` (objeto Alpine) e exibidos inline abaixo de cada campo.
- `globalError` é exibido no topo do formulário para erros do servidor.

### 6.3. Submissão em Duas Etapas

1. Primeiro: POST/PUT `/api/v1/processos` → cria/atualiza o processo.
2. Segundo (se `withConfig=true`): POST/PUT configuração → cria/atualiza a configuração.
3. Se o passo 1 falha, o passo 2 não é executado.
4. Após sucesso, `window.location.href` redireciona para `/processos/{id}`.

---

## 7. Casos de Teste

### 7.1. UC-01 — Criar Processo

- ✅ Criar processo com todos os campos preenchidos → processo aparece na página de detalhe
- ✅ Criar processo com configuração mínima (apenas URLs) → defaults aplicados
- ✅ `x-model` nos campos de texto (nome, descrição) → binding funcional
- ✅ `x-model.number` nos campos numéricos (timeout, max_retries) → valores numéricos enviados
- ✅ `x-model` no select (status, formato_saida) → opção correta enviada
- ✅ `x-model` no textarea (URLs) → múltiplas URLs parseadas corretamente
- ✅ `x-model` no checkbox (use_browser) → boolean enviado

### 7.2. UC-01 Variações — Campos Condicionais

- ✅ Selecionar `agendamento_tipo = recorrente` → campo cron aparece (`x-show`)
- ✅ Selecionar `agendamento_tipo = one_time` → campo datetime aparece (`x-show`)
- ✅ Selecionar `agendamento_tipo = manual` → campos cron e datetime desaparecem
- ✅ Selecionar `metodo_extracao = docling` → aviso SPA aparece
- ✅ Selecionar `metodo_extracao = html2text` → aviso SPA desaparece

### 7.3. UC-02 — Validação

- ✅ Nome vazio → erro inline visível, nenhuma request HTTP feita
- ✅ URLs vazias (com config) → erro inline visível
- ✅ Timeout = 0 → erro inline
- ✅ Timeout = 100000 → erro inline
- ✅ Cron inválido com agendamento recorrente → erro inline
- ✅ Nome duplicado (API 409) → `globalError` exibido no topo do formulário
- ✅ Após corrigir erro → erro inline desaparece

### 7.4. UC-03 — Editar Processo

- ✅ Acessar `/processos/{id}/editar` → campos pré-populados com dados existentes
- ✅ Campo nome pré-populado → valor correto exibido
- ✅ Campo URLs pré-populado → URLs existentes exibidas
- ✅ Campo timeout pré-populado → valor numérico correto
- ✅ Alterar nome e salvar → PUT enviado (não POST), dados atualizados na página de detalhe
- ✅ Alterar configuração e salvar → configuração atualizada

---

## 8. Critérios de Aceite

- [ ] Teste cria processo com configuração completa e verifica na página de detalhe.
- [ ] Campos condicionais (`x-show`) aparecem/desaparecem conforme seleção.
- [ ] Validação client-side exibe erros inline sem fazer request HTTP.
- [ ] Erro de servidor (409) exibe `globalError` no topo do formulário.
- [ ] Formulário de edição pré-popula campos com dados existentes.
- [ ] PUT é usado na edição (não POST).
- [ ] Todos os testes passam com `make test-e2e`.
- [ ] `make test` continua passando sem alterações.

---

## 9. Notas e Observações

### 9.1. Unicidade de Nomes

Para evitar conflitos entre testes, cada teste deve gerar nomes únicos. Usar timestamp ou UUID no nome:

```python
import time
nome = f"Processo E2E {int(time.time())}"
```

### 9.2. Timing do Alpine.js

Alpine.js pode demorar alguns milissegundos para processar o `x-data`. Antes de interagir com campos Alpine, aguardar:

```python
page.goto("/processos/novo")
# Aguardar Alpine processar o componente
page.wait_for_function("() => typeof Alpine !== 'undefined'")
```

### 9.3. Limpeza de Dados

Como o banco é compartilhado na sessão, processos criados por um teste podem aparecer na listagem de outro. Isso é aceitável para E2E — os testes devem ser resilientes a dados pré-existentes (usar seletores específicos, não contar total de linhas).
