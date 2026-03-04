# Backlog de Melhorias e Correções — Toninho

Gerado em: 2026-03-04
Fontes: análise de logs de containers, execução de testes do tutorial, revisão de código.

---

## Bugs

| ID | Título | Prioridade | Módulo | Descrição |
|---|---|---|---|---|
| BUG-001 | Task de agendamento não registrada no worker | 🔴 Crítica | `workers/tasks/agendamento_task.py` | O decorator registra a task com nome `"toninho.workers.verificar_agendamentos"`, mas o Beat a chama como `"toninho.workers.tasks.agendamento_task.verificar_agendamentos"`. Worker lança `KeyError` a cada 60s. **Fix**: alinhar o nome no `@celery_app.task(name=...)` com o definido em `celery_app.py`. |
| BUG-002 | `duracao_segundos` retorna `0` para execuções < 1s | 🟡 Média | `schemas/execucao.py` | `int((finalizado_em - iniciado_em).total_seconds())` arredonda para baixo, retornando `0` quando a execução leva menos de 1 segundo. **Fix**: usar `float` ou representar em milissegundos. |
| BUG-003 | SQLAlchemy em modo verbose nos containers | 🟡 Média | `core/config.py` / `core/database.py` | Todas as queries SQL aparecem como `INFO` nos logs do worker e da API. Em containers de produção isso polui o log e dificulta debugging real. **Fix**: configurar `echo=False` no engine e/ou ajustar nível do logger `sqlalchemy.engine` para `WARNING` quando `DEBUG=False`. |

---

## Melhorias

| ID | Título | Prioridade | Módulo | Descrição |
|---|---|---|---|---|
| MH-001 | Campo `contexto` dos logs sempre nulo | 🟠 Alta | `workers/tasks/execucao_task.py` | Logs salvos no DB têm `contexto=null`. Perda de informação estruturada (URL sendo processada, tentativa, tamanho). **Sugestão**: popular com dict `{"url": ..., "tentativa": ..., "bytes": ...}` nos eventos-chave. |
| MH-002 | YAML frontmatter em inglês vs. API em português | 🟠 Alta | `extraction/markdown_converter.py` | Arquivo `.md` gerado usa `title`, `extracted_at`, `extractor` (inglês). API/modelos usam `titulo`, `iniciado_em` (PT-BR). **Sugestão**: padronizar um idioma ou tornar configurável. |
| MH-003 | Suporte a páginas com JavaScript (SPAs) | 🟠 Alta | `extraction/http_client.py` | `httpx` não executa JS. Sites como React/Angular retornam HTML vazio. **Sugestão**: adicionar modo opcional com Playwright (`playwright.async_api`) controlado por flag `use_browser: bool` na configuração. |
| MH-004 | Endpoint para cancelar execução em andamento | 🟡 Média | `api/routes/execucoes.py` | Não existe endpoint `DELETE /api/v1/execucoes/{id}` ou `POST /api/v1/execucoes/{id}/cancelar`. Usuário não consegue parar uma extração longa. **Sugestão**: implementar endpoint que revoga a task Celery (`celery_app.control.revoke(task_id, terminate=True)`) e atualiza status para `CANCELADO`. |
| MH-005 | Rate limiting nas requisições HTTP de extração | 🟡 Média | `extraction/http_client.py` | Sem delay entre requests ao mesmo domínio. Servidores podem bloquear o extrator por excesso de requisições. **Sugestão**: adicionar `delay_between_requests: float` e `respect_robots_txt: bool` na configuração. |
| MH-006 | `output_dir` normalizado silenciosamente | 🟢 Baixa | `schemas/configuracao.py` | `validate_path` converte `"./output"` → `"output"` sem aviso. Pode confundir usuários que esperam o caminho exato que enviaram. **Sugestão**: documentar o comportamento ou retornar aviso no response. |
| MH-007 | Estrutura de diretório de output não documentada | 🟢 Baixa | `docs/` | O output real é `{output_dir}/{processo_id}/{execucao_id}/{arquivo}.md`, mas isso não está documentado na API nem nos schemas. Usuário precisa inferir via `caminho_arquivo` na resposta. **Sugestão**: adicionar ao Swagger description do endpoint. |

---

## Tech Debt

| ID | Título | Prioridade | Módulo | Descrição |
|---|---|---|---|---|
| TD-001 | Endpoint de health check comentado | 🟡 Média | `main.py` | `app.include_router(health.router...)` está comentado. Existe um `@app.get("/api/v1/health")` inline no `main.py`. **Sugestão**: desfazer comentário ou remover duplicata. |
| TD-002 | `duracao_segundos` duplicado em 3 schemas | 🟢 Baixa | `schemas/execucao.py` | Propriedade `@computed_field duracao_segundos` implementada 3x (`ExecucaoResponse`, `ExecucaoSummary`, `ExecucaoDetail`). **Sugestão**: extrair para mixin `DuracaoMixin` ou schema base. |
| TD-003 | Sem testes para `ExtractionOrchestrator` | 🟠 Alta | `tests/` | O fluxo central de extração (`workers/tasks/execucao_task.py` + `extraction/`) não tem cobertura de testes de integração. **Sugestão**: adicionar testes com mock de `HTTPClient` e `StorageInterface`. |
| TD-004 | `docker-compose.yml` sem healthcheck para API | 🟢 Baixa | `docker-compose.yml` | O container `api` não tem `healthcheck` definido. Worker depende de `api` com `depends_on` sem condição de saúde. **Sugestão**: adicionar `healthcheck` em `api` apontando para `/api/v1/health`. |
