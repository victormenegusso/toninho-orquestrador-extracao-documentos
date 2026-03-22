# PRD-ORG-008: Atualização do Backlog

**Status**: 📋 Planejado
**Prioridade**: 🟡 Baixa
**Categoria**: Documentação
**Tipo**: Manutenção

---

## 1. Objetivo

Atualizar o arquivo `docs/demandas/backlog.md` para refletir o estado real do projeto, marcando items já implementados e adicionando novos items identificados no discovery.

## 2. Contexto e Justificativa

O backlog foi gerado em 2026-03-04 e contém items que já foram implementados mas não foram marcados. Isso gera confusão sobre o que precisa ser feito.

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: D6

---

## 3. Verificações Necessárias

O agente deve verificar **no código** o status de cada item do backlog:

### 3.1. Bugs — Verificar no Código

| ID | Título | Verificar em |
|---|---|---|
| BUG-001 | Task de agendamento não registrada | `toninho/workers/tasks/agendamento_task.py` — verificar se o `name=` no decorator `@celery_app.task()` está alinhado com o nome registrado em `celery_app.py` |
| BUG-002 | `duracao_segundos` retorna 0 para < 1s | `toninho/schemas/execucao.py` — verificar se usa `int()` ou `float()` |
| BUG-003 | SQLAlchemy verbose nos containers | `toninho/core/database.py` e `toninho/core/config.py` — verificar se `echo=False` quando `DEBUG=False` |

### 3.2. Melhorias — Verificar no Código

| ID | Título | Verificar em | Status Esperado |
|---|---|---|---|
| MH-001 | Campo `contexto` dos logs sempre nulo | `toninho/workers/tasks/execucao_task.py` | Verificar |
| MH-002 | YAML frontmatter EN vs API PT-BR | `toninho/extraction/markdown_converter.py` | Verificar |
| MH-003 | Suporte a SPAs (Playwright) | `toninho/extraction/browser_client.py`, `toninho/models/configuracao.py` (campo `use_browser`) | ✅ **Provavelmente implementado** (PRD-018) |
| MH-004 | Endpoint cancelar execução | `toninho/api/routes/execucoes.py` | Verificar |
| MH-005 | Rate limiting | `toninho/extraction/http_client.py` | Verificar |
| MH-006 | `output_dir` normalizado | `toninho/schemas/configuracao.py` | Verificar |
| MH-007 | Estrutura output não documentada | `docs/` | Verificar |

### 3.3. Tech Debt — Verificar no Código

| ID | Título | Verificar em | Status Esperado |
|---|---|---|---|
| TD-001 | Health check comentado | `toninho/main.py` | Verificar se `health.router` está incluído |
| TD-002 | `duracao_segundos` duplicado | `toninho/schemas/execucao.py` | Verificar |
| TD-003 | Sem testes para Orchestrator | `tests/` | Verificar se existem testes para `ExtractionOrchestrator` |
| TD-004 | Docker sem healthcheck API | `docker-compose.yml` | ✅ **Implementado** (linhas 40-44 do compose) |

---

## 4. Alterações no Backlog

### 4.1. Para Items Implementados

Adicionar coluna "Status" e marcar como resolvido:

```markdown
| ID | Título | Prioridade | Módulo | Status |
|---|---|---|---|---|
| MH-003 | Suporte a SPAs (Playwright) | 🟠 Alta | extraction | ✅ Implementado (PRD-018) |
```

### 4.2. Novos Items a Adicionar

Baseados no discovery:

| ID | Título | Prioridade | Categoria | Descrição |
|---|---|---|---|---|
| TD-005 | README desatualizado | 🔴 Alta | Docs | README menciona Black/isort/flake8 em vez de Ruff. Links para dirs inexistentes. (PRD-ORG-001) |
| TD-006 | Falta doc de arquitetura | 🔴 Alta | Docs | Não existe documento unificado de arquitetura. (PRD-ORG-002) |
| TD-007 | Docker build redundante | 🟠 Alta | DevOps | 4 serviços fazem build do mesmo Dockerfile. (PRD-ORG-006) |
| TD-008 | Bug formulário pré-preenchido | 🟠 Alta | Frontend | Campos não carregam na primeira navegação via HTMX. (PRD-ORG-007) |

### 4.3. Atualizar Data

Mudar "Gerado em: 2026-03-04" para "Atualizado em: {data atual}".

---

## 5. Critérios de Aceite

- [ ] Todos os items verificados no código (BUG-001 a TD-004)
- [ ] Items implementados marcados com ✅ e referência ao PRD
- [ ] Novos items adicionados (TD-005 a TD-008)
- [ ] Data atualizada
- [ ] Nenhum item falso-positivo (só marcar como implementado se confirmado no código)
- [ ] Documento em Português (PT-BR)

---

## 6. Ordem de Execução

Este PRD deve ser executado **por último**, pois os demais PRDs podem resolver items do backlog. A verificação final garante que o backlog reflete o estado real pós-organização.

---

## 7. Fontes de Informação

O agente deve ler:
- `docs/demandas/backlog.md` — backlog atual
- Todos os arquivos referenciados na coluna "Verificar em" da seção 3
- `docs/prd/PRD-018-Integracao-Docling.md` — confirmar escopo do MH-003
