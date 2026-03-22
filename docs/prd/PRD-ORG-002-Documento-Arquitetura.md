# PRD-ORG-002: Documento de Arquitetura

**Status**: ✅ Implementado
**Prioridade**: 🔴 Alta
**Categoria**: Documentação
**Tipo**: Novo Documento

---

## 1. Objetivo

Criar o documento `docs/ARCHITECTURE.md` com a visão completa da arquitetura do sistema Toninho, incluindo estrutura de pastas, camadas, entidades, fluxos e comportamentos. Este documento deve ser a **referência principal** para humanos e IAs entenderem o sistema.

## 2. Contexto e Justificativa

O projeto não possui um documento de arquitetura unificado. Existe `docs/diagramas/arquitetura-fluxo-extracao.md` com apenas um flowchart Mermaid, e as decisões estão espalhadas em 7 ADRs. Um desenvolvedor ou agente de IA precisa ler múltiplos arquivos para entender o sistema completo.

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: D2

---

## 3. Conteúdo Obrigatório

O documento `docs/ARCHITECTURE.md` deve conter **todas** as seções abaixo, baseadas no estado real do código.

### 3.1. Visão Geral

Parágrafo descritivo: Toninho é um sistema de extração de documentos web que converte HTML em Markdown. Usa FastAPI para API REST, Celery para processamento assíncrono, SQLAlchemy para persistência, e HTMX + Alpine.js para interface web.

### 3.2. Stack Tecnológica

Tabela com **todas** as tecnologias e versões reais (extraídas do `pyproject.toml`):

| Componente | Tecnologia | Função |
|-----------|-----------|--------|
| Framework Web | FastAPI | API REST + serve templates |
| ORM | SQLAlchemy 2.x | Mapeamento objeto-relacional |
| Validação | Pydantic 2.x | DTOs e validação de dados |
| Task Queue | Celery | Processamento assíncrono |
| Message Broker | Redis | Broker + Result backend |
| Database (dev) | SQLite | Desenvolvimento local |
| Database (prod) | PostgreSQL | Produção |
| Logging | Loguru | Logging estruturado |
| HTTP Client | httpx | Requisições HTTP |
| HTML Parsing | BeautifulSoup4 + lxml | Parsing de HTML |
| HTML→Markdown | html2text | Conversão |
| Extração Avançada | Docling (IBM) | Extração semântica |
| Browser | Playwright | Renderização de SPAs |
| Templates | Jinja2 | Server-side rendering |
| CSS | TailwindCSS | Utility-first CSS |
| Interatividade | HTMX + Alpine.js | Frontend reativo sem SPA |
| Linter/Formatter | Ruff | Linting e formatação |
| Type Checker | mypy | Verificação de tipos |
| Security | Bandit | Análise de segurança |
| Testes | pytest + Playwright | Unit, integration, E2E |
| CI/CD | GitHub Actions | Pipeline automatizado |

### 3.3. Estrutura de Pastas

Árvore completa com descrição de cada diretório e arquivo principal:

```
toninho-processo-extracao/
├── toninho/                     # Código fonte principal (backend)
│   ├── api/                    # Camada de API (FastAPI routes)
│   │   ├── routes/             # Endpoints organizados por domínio
│   │   │   ├── processos.py    # CRUD de processos
│   │   │   ├── configuracoes.py# Configuração de extração
│   │   │   ├── execucoes.py    # Execuções e status
│   │   │   ├── paginas_extraidas.py # Conteúdo extraído
│   │   │   ├── logs.py         # Logs com SSE
│   │   │   ├── monitoring.py   # Métricas do sistema
│   │   │   ├── health.py       # Health check
│   │   │   └── frontend.py     # Serve templates HTML
│   │   └── dependencies.py     # Injeção de dependências (get_db, etc)
│   ├── services/               # Camada de Serviço (lógica de negócio)
│   │   ├── processo_service.py
│   │   ├── configuracao_service.py
│   │   ├── execucao_service.py
│   │   ├── pagina_extraida_service.py
│   │   └── log_service.py
│   ├── repositories/           # Camada de Repositório (acesso a dados)
│   │   ├── processo_repository.py
│   │   ├── configuracao_repository.py
│   │   ├── execucao_repository.py
│   │   ├── pagina_extraida_repository.py
│   │   └── log_repository.py
│   ├── models/                 # Modelos SQLAlchemy (ORM)
│   │   ├── base.py             # Base model com TimestampMixin
│   │   ├── processo.py
│   │   ├── configuracao.py
│   │   ├── execucao.py
│   │   ├── pagina_extraida.py
│   │   ├── log.py
│   │   └── enums.py            # Enums de status
│   ├── schemas/                # Schemas Pydantic (DTOs)
│   │   ├── processo.py
│   │   ├── configuracao.py
│   │   ├── execucao.py
│   │   ├── pagina_extraida.py
│   │   ├── log.py
│   │   ├── validators.py       # Validadores customizados
│   │   └── responses.py        # Formato padrão de resposta
│   ├── workers/                # Celery workers e tasks
│   │   ├── celery_app.py       # Configuração do Celery
│   │   ├── tasks/
│   │   │   ├── execucao_task.py    # Task principal de extração
│   │   │   ├── agendamento_task.py # Verificação de agendamentos
│   │   │   └── limpeza_task.py     # Limpeza de logs antigos
│   │   └── utils.py            # ExtractionOrchestrator
│   ├── extraction/             # Módulo de extração (autônomo)
│   │   ├── extractor.py        # PageExtractor principal
│   │   ├── http_client.py      # Cliente HTTP (httpx)
│   │   ├── browser_client.py   # Cliente Playwright
│   │   ├── markdown_converter.py # HTML → Markdown
│   │   ├── storage.py          # Armazenamento de arquivos
│   │   └── utils.py            # Sanitização e helpers
│   ├── monitoring/             # Health checks e métricas
│   ├── core/                   # Infraestrutura
│   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   ├── database.py         # Engine, SessionLocal, get_db()
│   │   ├── logging.py          # Configuração Loguru
│   │   └── exceptions.py       # Exceções customizadas
│   └── main.py                 # Entry point FastAPI
├── frontend/                   # Interface web
│   ├── templates/              # Templates Jinja2
│   │   ├── base.html           # Layout master
│   │   ├── layouts/            # Layouts (dashboard)
│   │   ├── components/         # Componentes reutilizáveis
│   │   ├── pages/              # Páginas por domínio
│   │   └── partials/           # Fragmentos HTMX
│   └── static/                 # CSS, JS, imagens
├── tests/                      # Testes automatizados
│   ├── unit/                   # Testes unitários
│   ├── integration/            # Testes de integração
│   ├── e2e/                    # Testes E2E (Playwright)
│   ├── fixtures/               # Geradores de dados de teste
│   └── conftest.py             # Fixtures compartilhadas
├── migrations/                 # Alembic (migrações de DB)
├── scripts/                    # Scripts utilitários
├── docs/                       # Documentação completa
├── Dockerfile                  # Build multi-stage
├── docker-compose.yml          # Orquestração de serviços
├── docker-compose.override.yml # Overrides para dev
├── pyproject.toml              # Dependências e config de ferramentas
├── Makefile                    # Comandos de desenvolvimento
└── entrypoint.sh               # Script de entrada Docker
```

### 3.4. Arquitetura em Camadas

Diagrama da arquitetura (usar Mermaid ou texto ASCII):

```
┌─────────────────────────────────────────────────┐
│                    FRONTEND                      │
│         HTMX + Alpine.js + Jinja2               │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│              API LAYER (FastAPI)                 │
│  routes/ → Validação Pydantic → Depends()       │
└──────┬───────────────────────────────┬──────────┘
       ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│  SERVICE LAYER   │          │  CELERY WORKERS  │
│  Lógica negócio  │          │  Tasks assíncr.  │
└──────┬───────────┘          └──────┬───────────┘
       ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│ REPOSITORY LAYER │          │ EXTRACTION MODULE│
│ SQLAlchemy ORM   │          │ HTTP/Playwright  │
└──────┬───────────┘          │ HTML→Markdown    │
       ↓                      └──────────────────┘
┌──────────────────┐
│    DATABASE       │
│ SQLite / Postgres │
└──────────────────┘
```

**Regras de dependência:**
- API → Service → Repository → Model (nunca o inverso)
- Workers acessam Services diretamente
- Extraction é autônomo (não depende de nenhuma outra camada)
- Injeção de dependência via FastAPI `Depends()`

### 3.5. Entidades e Ciclo de Vida

#### Processo
```
Criação → ATIVO ←→ INATIVO → ARQUIVADO
                    ↑
              (pode reativar)
```

- **ATIVO**: Pode receber configurações e execuções
- **INATIVO**: Pausado, não aceita novas execuções
- **ARQUIVADO**: Soft-delete, mantém histórico

#### Configuração
- Relação: N→1 com Processo
- Imutável após criação (cria nova versão para alterar)
- Campos: urls[], timeout, max_retries, formato_saida, metodo_extracao, use_browser

#### Execução
```
CRIADO → AGUARDANDO → EM_EXECUCAO → CONCLUIDO
                                   → FALHOU
                                   → CONCLUIDO_COM_ERROS
                      CANCELADO ←──┘
         PAUSADO ←────┘
```

- **CRIADO**: Registro no DB, Celery task enfileirada
- **AGUARDANDO**: Na fila do Redis
- **EM_EXECUCAO**: Worker processando URLs
- **CONCLUIDO**: Todas as páginas extraídas com sucesso
- **CONCLUIDO_COM_ERROS**: Algumas páginas falharam
- **FALHOU**: Erro fatal na execução
- **CANCELADO**: Revogado pelo usuário

#### PáginaExtraída
- Relação: N→1 com Execução
- Armazena: URL original, caminho do arquivo .md, status, tamanho

#### Log
- Relação: N→1 com Execução
- Níveis: DEBUG, INFO, WARNING, ERROR
- Streaming via SSE (Server-Sent Events)

### 3.6. Métodos de Extração

| Método | Tecnologia | Use Case | JS Support | Velocidade |
|--------|-----------|----------|------------|------------|
| HTML2TEXT | httpx + BeautifulSoup + html2text | Sites estáticos | ❌ | ⚡ Rápido |
| DOCLING | IBM Docling | Docs complexos (PDFs, tabelas) | ❌ | 🐌 Lento |
| Browser | Playwright headless | SPAs (React, Angular) | ✅ | 🐌 Lento |

Seleção via campo `metodo_extracao` na Configuração. Browser mode ativado por `use_browser=True`.

### 3.7. Fluxo de Execução (Workflow Completo)

Documentar o fluxo de 3 passos:

1. **POST /api/v1/processos** → Criar processo
2. **POST /api/v1/processos/{id}/configuracoes** → Configurar URLs
3. **POST /api/v1/processos/{id}/execucoes** → Disparar execução

E o fluxo assíncrono do worker:
```
Celery Worker recebe task
  → Busca Execução + Configuração no DB
  → Atualiza status → EM_EXECUCAO
  → Para cada URL:
      → PageExtractor.extract(url)
      → Salva .md no filesystem
      → Cria PáginaExtraída no DB
      → Registra Log
  → Calcula métricas (páginas, bytes, taxa_erro)
  → Atualiza status final
  → Emite updates via WebSocket/SSE
```

### 3.8. Infraestrutura Docker

Documentar os 5 serviços:

| Serviço | Porta | Função |
|---------|-------|--------|
| redis | 6379 | Message broker + result backend |
| api | 8000 | FastAPI (API + Frontend) |
| worker | — | Celery worker (processa extrações) |
| beat | — | Celery Beat (tarefas agendadas) |
| flower | 5555 | Monitoramento de tasks |

### 3.9. Formato de Resposta da API

```json
{
  "success": true,
  "data": { },
  "meta": { "page": 1, "per_page": 10, "total": 5 }
}
```

### 3.10. Referências

Links para ADRs relevantes:
- ADR-001 (Stack), ADR-002 (Async), ADR-003 (DB), ADR-004 (Camadas), ADR-005 (Extração), ADR-006 (Frontend), ADR-007 (Qualidade)

---

## 4. Critérios de Aceite

- [ ] Arquivo `docs/ARCHITECTURE.md` criado
- [ ] Todas as 10 seções presentes (3.1 a 3.10)
- [ ] Estrutura de pastas reflete o estado real do código (verificar com `find`)
- [ ] Diagramas de ciclo de vida das entidades presentes
- [ ] Stack tecnológica com versões extraídas do `pyproject.toml`
- [ ] Documento em Português (PT-BR)
- [ ] Referências cruzadas para ADRs

---

## 5. Fontes de Informação

O agente deve extrair informação de:
- `pyproject.toml` → versões das dependências
- `toninho/models/enums.py` → estados das entidades
- `toninho/api/routes/` → endpoints existentes
- `toninho/workers/` → fluxo de execução
- `toninho/extraction/` → métodos de extração
- `docker-compose.yml` → serviços Docker
- `docs/adr/` → decisões de arquitetura
