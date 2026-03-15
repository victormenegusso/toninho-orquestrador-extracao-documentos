# Prompt de Implementação — Testes E2E Playwright (PRD-019 a PRD-025)

> **Este documento é um prompt para ser passado a um agente de IA que executará a implementação dos testes E2E com Playwright no projeto Toninho.**

---

## Contexto

Você vai implementar testes End-to-End (E2E) para o frontend do projeto **Toninho — Sistema de Extração de Documentos**. O projeto usa FastAPI + HTMX + Alpine.js + Tailwind CSS + Jinja2. Os testes usam **Playwright** com **pytest-playwright**.

O trabalho está dividido em **7 PRDs** (Product Requirements Documents) que devem ser executados **sequencialmente**. Cada PRD contém todos os detalhes necessários: objetivo, estrutura de arquivos, fixtures, seletores de elementos, exemplos de código e critérios de aceite.

---

## Regras de Execução

1. **Este é um plano sequencial.** Cada PRD deve ser implementado **individualmente**, do início ao fim, antes de avançar para o próximo.

2. **Não avance para o próximo PRD** até que todos os critérios de aceite do PRD atual estejam satisfeitos e os testes passem.

3. **Após completar cada PRD**, execute `make test-e2e` para validar que todos os testes (incluindo os de PRDs anteriores) continuam passando.

4. **Se encontrar inconsistências** entre o PRD e o código real (seletores que não existem, endpoints com assinatura diferente, etc.), adapte a implementação ao código real — o PRD é um guia, não uma especificação rígida.

5. **Mantenha commits granulares** — um commit por PRD completado, com mensagem descritiva.

---

## Ordem de Implementação

Execute os PRDs exatamente nesta ordem:

### PRD-019 — Setup e Infraestrutura Playwright
**Arquivo:** `docs/prd/PRD-019-implementacao-playwright-setup-infraestrutura.md`
**O que faz:**
- Instala dependências (`playwright`, `pytest-playwright`).
- Configura `pyproject.toml` (markers, dependências).
- Cria targets no `Makefile` (`test-e2e` headless e `test-e2e-headed` com browser visível).
- Cria `tests/e2e/conftest.py` com `live_server` fixture (uvicorn em subprocess com SQLite temporário).
- Cria `tests/e2e/test_smoke.py` com testes de validação da infraestrutura.
**Critério de saída:** `make test-e2e` executa e os smoke tests passam.

---

### PRD-020 — CRUD de Processos (UC-01, UC-02, UC-03)
**Arquivo:** `docs/prd/PRD-020-implementacao-playwright-crud-processos.md`
**O que faz:**
- Cria `tests/e2e/test_uc01_criar_processo.py` — formulário Alpine.js completo.
- Cria `tests/e2e/test_uc02_validacao_formulario.py` — validação client-side.
- Cria `tests/e2e/test_uc03_editar_processo.py` — edição com valores pré-carregados.
- Adiciona fixtures de seeding: `create_processo`, `create_processo_com_config`.
**Critério de saída:** Todos os testes de UC-01/02/03 passam + smoke tests continuam verdes.

---

### PRD-021 — Listagem, Busca e Ações em Processos (UC-04, UC-05, UC-06)
**Arquivo:** `docs/prd/PRD-021-implementacao-playwright-listagem-busca-processos.md`
**O que faz:**
- Cria `tests/e2e/test_uc04_buscar_processos.py` — HTMX search com debounce.
- Cria `tests/e2e/test_uc05_executar_processo.py` — diálogo `hx-confirm`.
- Cria `tests/e2e/test_uc06_deletar_processo.py` — delete com animação.
**Critério de saída:** Todos os testes de UC-04/05/06 passam + testes anteriores continuam verdes.

---

### PRD-022 — Dashboard com Polling Duplo (UC-07)
**Arquivo:** `docs/prd/PRD-022-implementacao-playwright-dashboard-polling.md`
**O que faz:**
- Cria `tests/e2e/test_uc07_dashboard.py` — polling duplo (stats 5s + execuções 3s).
- Testa `hx-trigger="every Xs"` com `page.expect_response`.
- Testa quick action links e cards de estatísticas.
**Critério de saída:** Todos os testes de UC-07 passam + testes anteriores continuam verdes.

---

### PRD-023 — Execuções: Ciclo de Vida (UC-09, UC-10)
**Arquivo:** `docs/prd/PRD-023-implementacao-playwright-execucoes-ciclo-vida.md`
**O que faz:**
- Cria `tests/e2e/test_uc09_pausar_retomar_cancelar.py` — botões condicionais por status, `hx-confirm`.
- Cria `tests/e2e/test_uc10_listar_execucoes.py` — listagem com filtros e badges.
- Adiciona fixtures: `create_execucao`, `update_execucao_status`.
**Critério de saída:** Todos os testes de UC-09/10 passam + testes anteriores continuam verdes.

---

### PRD-024 — Logs em Tempo Real via SSE (UC-08)
**Arquivo:** `docs/prd/PRD-024-implementacao-playwright-logs-sse-tempo-real.md`
**O que faz:**
- Cria `tests/e2e/test_uc08_logs_sse.py` — EventSource, cores por nível, auto-scroll, filtro.
- Adiciona fixture `create_logs_batch`.
- Testa barra de progresso com polling HTMX (`every 2s`).
**Critério de saída:** Todos os testes de UC-08 passam + testes anteriores continuam verdes.

---

### PRD-025 — Páginas Extraídas, Notificações e Navegação (UC-11, UC-12, UC-13, UC-14)
**Arquivo:** `docs/prd/PRD-025-implementacao-playwright-paginas-notificacoes-navegacao.md`
**O que faz:**
- Cria `tests/e2e/test_uc11_paginas_extraidas.py` — grid HTMX, busca/filtro, preview modal, download.
- Cria `tests/e2e/test_uc12_notificacoes.py` — flash messages Alpine.js.
- Cria `tests/e2e/test_uc13_navegacao.py` — sidebar com `hx-boost`.
- Cria `tests/e2e/test_uc14_erros_rede.py` — resiliência HTMX, interceptação com `page.route()`.
- Adiciona fixture `create_paginas_extraidas`.
**Critério de saída:** Todos os testes de UC-11/12/13/14 passam + suite completa verde com `make test-e2e`.

---

## Referências do Projeto

| Recurso | Caminho |
|---|---|
| Casos de uso E2E | `docs/discoverys/e2e-front/casos_de_uso_e2e.md` |
| PRDs 019-025 | `docs/prd/PRD-019-*.md` a `docs/prd/PRD-025-*.md` |
| App principal | `toninho/main.py` |
| Configuração | `toninho/core/config.py` |
| Database | `toninho/core/database.py` |
| Templates frontend | `frontend/templates/` |
| Testes existentes | `tests/` |
| Conftest existente | `tests/conftest.py` |
| ADRs | `docs/adr/` |

## Observações Importantes

- O projeto usa **Poetry** para gerenciamento de dependências.
- O banco de dados de teste E2E é **SQLite temporário** (não o banco de desenvolvimento).
- **Playwright** precisa de `playwright install chromium` após instalação.
- Os templates usam **HTMX 1.9.10** + **Alpine.js 3.13.3** — verifique a documentação dessas versões para comportamentos específicos.
- O `Makefile` deve ter targets para execução **headless** (`make test-e2e`) e **headed** (`make test-e2e-headed` com `--headed --slowmo 500`).
- Cada PRD contém **seletores de elementos**, **exemplos de código** e **regras de negócio** detalhados — leia o PRD inteiro antes de começar a implementar.
