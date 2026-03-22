# Backlog de Melhorias e Correções — Toninho

Atualizado em: 2025-07-11
Fontes: análise de logs de containers, execução de testes do tutorial, revisão de código, verificação automatizada no código-fonte.

---

## Bugs

| ID | Título | Prioridade | Módulo | Status | Descrição |
|---|---|---|---|---|---|
| BUG-001 | Task de agendamento não registrada no worker | 🔴 Crítica | `workers/tasks/agendamento_task.py` | ✅ Corrigido | Nome no `@celery_app.task(name=...)` alinhado com `celery_app.py`. Task usa `"toninho.workers.tasks.agendamento_task.verificar_agendamentos"` em ambos. |
| BUG-002 | `duracao_segundos` retorna `0` para execuções < 1s | 🟡 Média | `schemas/execucao.py` | ✅ Corrigido | Agora usa `float` com `round(..., 3)` via `DuracaoMixin`, retornando precisão em milissegundos. |
| BUG-003 | SQLAlchemy em modo verbose nos containers | 🟡 Média | `core/config.py` / `core/database.py` | ✅ Corrigido | `SQL_ECHO: bool = False` no config. Engine usa `echo=settings.SQL_ECHO`, desabilitado por padrão. |

---

## Melhorias

| ID | Título | Prioridade | Módulo | Status | Descrição |
|---|---|---|---|---|---|
| MH-001 | Campo `contexto` dos logs sempre nulo | 🟠 Alta | `workers/utils.py` | ✅ Implementado | Campo `contexto` agora populado com dicts estruturados (`{"url": ..., "indice": ..., "total": ...}`) nos eventos-chave de extração. |
| MH-002 | YAML frontmatter em inglês vs. API em português | 🟠 Alta | `extraction/markdown_converter.py` | ✅ Corrigido | Frontmatter agora usa chaves em PT-BR (`titulo`, `extraido_em`, `extrator`), alinhado com a API. |
| MH-003 | Suporte a páginas com JavaScript (SPAs) | 🟠 Alta | `extraction/browser_client.py` | ✅ Implementado (PRD-018) | `BrowserClient` com Playwright implementado. Flag `use_browser: bool` na configuração controla o modo. |
| MH-004 | Endpoint para cancelar execução em andamento | 🟡 Média | `api/routes/execucoes.py` | ✅ Implementado | `POST /api/v1/execucoes/{id}/cancelar` implementado com revogação de task Celery e atualização de status. |
| MH-005 | Rate limiting nas requisições HTTP de extração | 🟡 Média | `extraction/http_client.py` | ✅ Implementado | `delay_between_requests` com controle por domínio + `respect_robots_txt` com cache de robots.txt por origem. |
| MH-006 | `output_dir` normalizado silenciosamente | 🟢 Baixa | `schemas/configuracao.py` | ✅ Documentado | Comportamento documentado no schema: "Caminhos relativos com `./` são normalizados automaticamente". |
| MH-007 | Estrutura de diretório de output não documentada | 🟢 Baixa | `docs/` | ✅ Documentado | Estrutura `{output_dir}/{processo_id}/{execucao_id}/{slug}.md` documentada em ARCHITECTURE.md (seção Armazenamento), API.md (seção 7.6) e nos schemas. |

---

## Tech Debt

| ID | Título | Prioridade | Módulo | Status | Descrição |
|---|---|---|---|---|---|
| TD-001 | Endpoint de health check comentado | 🟡 Média | `main.py` | ✅ Corrigido | `app.include_router(health.router)` ativo na linha 40 do `main.py`. Sem duplicatas. |
| TD-002 | `duracao_segundos` duplicado em 3 schemas | 🟢 Baixa | `schemas/execucao.py` | ✅ Corrigido | Extraído para `DuracaoMixin`, reutilizado em `ExecucaoResponse`, `ExecucaoSummary` e `ExecucaoDetail`. |
| TD-003 | Sem testes para `ExtractionOrchestrator` | 🟠 Alta | `tests/` | ✅ Implementado | `tests/unit/workers/test_orchestrator.py` (508 linhas) + testes em `test_tasks.py` e `test_workers_docling.py`. |
| TD-004 | `docker-compose.yml` sem healthcheck para API | 🟢 Baixa | `docker-compose.yml` | ✅ Implementado (PRD-ORG-006) | Healthcheck configurado com `curl -f http://localhost:8000/api/v1/health`. Worker usa `depends_on` com `condition: service_healthy`. |

---

## Novos Items (identificados na reorganização)

| ID | Título | Prioridade | Categoria | Status | Descrição |
|---|---|---|---|---|---|
| TD-005 | README desatualizado | 🔴 Alta | Docs | ✅ Corrigido (PRD-ORG-001) | README mencionava Black/isort/flake8, links quebrados. Atualizado com Ruff e links corretos. |
| TD-006 | Falta documentação de arquitetura | 🔴 Alta | Docs | ✅ Implementado (PRD-ORG-002) | `docs/ARCHITECTURE.md` criado com visão completa do sistema. |
| TD-007 | Docker build redundante | 🟠 Alta | DevOps | ✅ Corrigido (PRD-ORG-006) | Serviço `api` faz build único com `image: toninho:latest`. Worker/beat/flower reutilizam a imagem. |
| TD-008 | Sem teste anti-regressão de formulários | 🟠 Alta | Frontend | ✅ Implementado (PRD-ORG-007) | `tests/e2e/test_uc15_formulario_pre_preenchido.py` criado com 4 cenários. |
| MH-008 | `respect_robots_txt` não implementado | 🟢 Baixa | `extraction/http_client.py` | ✅ Implementado | `RobotsChecker` com cache por domínio. Campo `respect_robots_txt: bool` em model, schema e frontend. Migration adicionada. |
| MH-009 | Estrutura de output mais visível na documentação | 🟢 Baixa | `docs/` | ✅ Implementado | Seção adicionada em ARCHITECTURE.md (Estrutura de Diretórios de Output) e API.md (seção 7.6). |
