---
mode: agent
description: Plano de implementação para PRD-018 — Integração Docling como motor de extração
---

# Prompt: Plano de Implementação — PRD-018 Integração Docling

## Contexto do Projeto

Você está trabalhando no **Toninho**, um sistema Python de extração de conteúdo web para Markdown, com as seguintes características definidas nos ADRs do projeto:

### Stack (ADR-001)
- **API**: FastAPI 0.100+ com Pydantic v2, async, OpenAPI automático
- **ORM**: SQLAlchemy 2.x com Alembic para migrations
- **Task queue**: Celery + Redis (workers para extração assíncrona)
- **Frontend**: Jinja2 server-side + HTMX + Alpine.js + TailwindCSS
- **Logging**: Loguru
- **Banco dev**: SQLite | **Banco prod**: PostgreSQL

### Arquitetura em camadas (ADR-004)
```
api/routes/ → services/ → repositories/ → models/
schemas/          (DTOs Pydantic)
workers/          (Celery tasks → ExtractionOrchestrator)
extraction/       (módulo autônomo: fetch, parse, markdown, storage)
```
- **Regra fundamental**: cada camada conhece apenas a camada imediatamente abaixo.
- Services são injetados via `Depends()` do FastAPI — sem acoplamento direto em rotas.
- `ExtractionOrchestrator` (em `workers/utils.py`) é o ponto de conexão entre o banco (DB) e o módulo `extraction/`.
- `extraction/` é desacoplado e pode ser usado standalone.

### Módulo de extração atual (ADR-005)
Pipeline atual: `URL → HTTPClient (httpx) → HTML → BeautifulSoup → html2text → Markdown → Storage`
- `StorageInterface` usa Strategy Pattern — não alterar.
- Arquivos `.md` gerados com YAML frontmatter (`url`, `titulo`, `extraido_em`, `extrator`).

### Processamento assíncrono (ADR-002)
- Task Celery `executar_processo_task` → `ExtractionOrchestrator.run(execucao_id)`.
- Retry automático configurável; erros de negócio (`ValueError`) **sem** retry.
- Workers são síncronos internamente; operações async são executadas via `asyncio.run()`.

### Banco de dados (ADR-003)
- Migrations via Alembic; agnóstico ao banco.
- `server_default` obrigatório em novas colunas para compatibilidade com registros existentes.
- Enums salvos como strings (`str, Enum`) para legibilidade.

### Frontend (ADR-006)
- Templates Jinja2 em `frontend/templates/`.
- Interações com Alpine.js (reatividade local) e HTMX (atualizações parciais).
- Formulários de criação/edição em `frontend/templates/pages/processos/create.html`.
- Dados iniciais do formulário passados como objetos JSON via `x-data` do Alpine.js.

### Qualidade (ADR-007)
- **Linter/formatter**: `ruff` (PEP8, isort, bugbear, pyupgrade, simplify)
- **Tipagem**: `mypy` (obrigatório para código em `toninho/`)
- **Segurança**: `bandit` — adicionar `# nosec BXX` apenas onde intencionalmente necessário
- **Testes**: `pytest` + `pytest-cov`, cobertura mínima **90%**
- Estrutura: `tests/unit/`, `tests/integration/`, `tests/e2e/`
- Mocks para dependências externas em testes unitários; `TestClient` + SQLite em memória para integração.

---

## Tarefa

Monte um **plano de implementação detalhado** para a demanda descrita no `PRD-018: Integração Docling como Motor de Extração` (arquivo `docs/prd/PRD-018-Integracao-Docling.md`).

### Regras para o plano

1. **Agrupe** implementações de frontend e API que pertencem ao mesmo caso de uso (ex: UC-07 cria configuração via API e UC-01 cria via front — devem ser implementados juntos, pois o frontend chama a API que chama o service).
2. **Respeite as dependências entre camadas**: sempre implemente na ordem `models → schemas → services/repositories → routes → workers → extraction → frontend`.
3. **Cada passo do plano deve ser atômico e verificável**: ao final de cada passo, o código deve compilar e, idealmente, os testes unitários daquele passo devem passar.
4. **Nunca pule a escrita de testes**: cada passo de implementação deve incluir os testes correspondentes (unitários e/ou de integração).
5. **Siga os padrões dos ADRs** acima em cada decisão técnica.

### Estrutura esperada do plano

Para cada passo, forneça:
- **O que implementar** (arquivos criados/alterados)
- **Casos de uso cobertos** (ex: UC-01, UC-07)
- **Camada(s) da arquitetura** envolvida(s)
- **Descrição técnica** clara e suficiente para implementação sem ambiguidade
- **Testes a escrever** (arquivo, cenários mínimos obrigatórios)
- **Verificação** — como confirmar que o passo está correto antes de avançar

### Passos esperados (referência — reorganize se necessário)

Use os passos abaixo como referência, mas agrupe e reorganize conforme as dependências e a regra de agrupar front+API relacionados:

**Passo 1 — Fundação: Enum + Model + Migration**
> UC-06 (migration em banco existente)
- `toninho/models/enums.py`: novo enum `MetodoExtracao`
- `toninho/models/configuracao.py`: novo campo `metodo_extracao`
- `migrations/versions/<hash>_add_metodo_extracao.py`: migration com `server_default="html2text"`
- Testes: enum possui valores corretos; model cria com default; migration `upgrade`/`downgrade`

**Passo 2 — Schema + API + Frontend: Configuração com novo motor**
> UC-01 (front), UC-07 (API criar), UC-08 (API atualizar), UC-09 (API consultar)
- `toninho/schemas/configuracao.py`: campo `metodo_extracao` em `ConfiguracaoCreate`, `ConfiguracaoUpdate`, `ConfiguracaoResponse`
- `frontend/templates/pages/processos/create.html`: seletor de motor + aviso de SPA (Alpine.js)
- Testes de schema: deserialização, default, serialização, update parcial
- Testes de API: POST cria com `docling`, GET retorna campo, PUT atualiza motor

**Passo 3 — Novo módulo de extração: DoclingPageExtractor**
> UC-02 (HTML estático), UC-03 (SPA + Playwright), UC-04 (falha)
- `toninho/extraction/docling_extractor.py`: classe `DoclingPageExtractor` com `extract()` e `extract_from_html()`
- Testes unitários com mock de `DocumentConverter`

**Passo 4 — Worker: ExtractionOrchestrator com roteamento de motor**
> UC-02, UC-03, UC-04, UC-10 (logs identificam motor)
- `toninho/workers/utils.py`: `_extract_url()` ramifica entre `PageExtractor` e `DoclingPageExtractor`
- Testes unitários com mock dos dois extratores

**Passo 5 — Dependência e infraestrutura**
- `pyproject.toml`: adicionar `docling>=2.0.0`
- `docker-compose.override.yml`: volume `docling_cache` no worker

**Passo 6 — Testes de integração e validação de cobertura**
- Testes de integração end-to-end: fluxo completo com banco SQLite em memória e mocks de Docling
- Verificar cobertura ≥ 90% com `make test`

---

## O que NÃO está no escopo desta implementação

- Suporte a PDF, DOCX ou OCR via Docling.
- Fallback automático entre motores.
- Campo `metodo_extracao` em `PaginaExtraida`.
- Mudança no fluxo de agendamento, execução ou status.
- Alteração nos schemas `ExecucaoResponse` ou `PaginaExtraidaResponse`.

---

## Arquivos-chave para leitura antes de implementar

Leia os seguintes arquivos para entender o código existente antes de qualquer alteração:

```
toninho/models/enums.py
toninho/models/configuracao.py
toninho/schemas/configuracao.py
toninho/extraction/extractor.py
toninho/extraction/markdown_converter.py
toninho/extraction/storage.py
toninho/workers/utils.py
toninho/workers/tasks/execucao_task.py
frontend/templates/pages/processos/create.html
migrations/env.py
pyproject.toml
```

---

## Entregável esperado

Um plano de implementação em markdown com **todos os passos numerados**, cada um com os itens definidos na seção "Estrutura esperada do plano". O plano deve ser suficientemente detalhado para que um desenvolvedor implemente sem precisar consultar o PRD novamente.
