# Arquitetura do Sistema — Toninho Processo Extração

> Documento de referência técnica para desenvolvedores e contribuidores do projeto.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Estrutura de Pastas](#3-estrutura-de-pastas)
4. [Arquitetura em Camadas](#4-arquitetura-em-camadas)
5. [Entidades e Ciclo de Vida](#5-entidades-e-ciclo-de-vida)
6. [Métodos de Extração](#6-métodos-de-extração)
7. [Fluxo de Execução (Workflow Completo)](#7-fluxo-de-execução-workflow-completo)
8. [Infraestrutura Docker](#8-infraestrutura-docker)
9. [Formato de Resposta da API](#9-formato-de-resposta-da-api)
10. [Referências](#10-referências)

---

## 1. Visão Geral

**Toninho** é um sistema de extração de documentos web que converte páginas HTML em Markdown estruturado. O projeto foi projetado para lidar com sites estáticos e aplicações de página única (SPAs) de forma resiliente e escalável.

**Principais características:**

- **API REST** com FastAPI para gerenciamento de processos, execuções e configurações.
- **Processamento assíncrono** via Celery + Redis para extrações de longa duração.
- **Persistência** com SQLAlchemy (SQLite em desenvolvimento, PostgreSQL em produção).
- **Interface web** reativa com HTMX + Alpine.js + Jinja2, sem necessidade de framework SPA.
- **Dois métodos de extração**: `html2text` (rápido, com suporte a SPA via Playwright) e `Docling` (IBM, extração semântica avançada).
- **Agendamento** de execuções recorrentes, únicas ou manuais com Celery Beat + croniter.

---

## 2. Stack Tecnológica

| Componente | Tecnologia | Versão | Função |
|---|---|---|---|
| **Linguagem** | Python | ^3.11 | Linguagem principal |
| **Framework Web** | FastAPI | ^0.109.0 | API REST + serve templates |
| **ORM** | SQLAlchemy | ^2.0.25 | Mapeamento objeto-relacional |
| **Validação** | Pydantic | ^2.5.3 | DTOs e validação de dados |
| **Settings** | pydantic-settings | ^2.1.0 | Configuração via variáveis de ambiente |
| **Task Queue** | Celery | ^5.3.6 | Processamento assíncrono de tasks |
| **Message Broker** | Redis | ^5.0.1 | Broker + result backend |
| **Database (dev)** | SQLite | — | Desenvolvimento local |
| **Database (prod)** | PostgreSQL | — | Produção |
| **Migrations** | Alembic | ^1.13.1 | Migrações de banco de dados |
| **Logging** | Loguru | ^0.7.2 | Logging estruturado |
| **HTTP Client** | httpx | ^0.26.0 | Requisições HTTP assíncronas |
| **HTML Parsing** | BeautifulSoup4 | ^4.14.3 | Parsing de HTML |
| **HTML Parsing** | lxml | ^6.0.2 | Parser XML/HTML de alto desempenho |
| **HTML→Markdown** | html2text | ^2025.4.15 | Conversão de HTML para Markdown |
| **Extração Avançada** | Docling (IBM) | >=2.0.0 | Extração semântica estruturada |
| **Browser** | Playwright | ^1.49.0 | Renderização de SPAs (headless Chromium) |
| **Templates** | Jinja2 | ^3.1.3 | Server-side rendering |
| **CSS** | TailwindCSS | — | Utility-first CSS framework |
| **Interatividade** | HTMX + Alpine.js | — | Frontend reativo sem SPA |
| **Server** | Uvicorn | ^0.27.0 | Servidor ASGI |
| **Monitoring** | Flower | ^2.0.1 | Dashboard de monitoramento de tasks |
| **Cron** | croniter | ^6.0.0 | Agendamento e parsing de expressões cron |
| **Linter/Formatter** | Ruff | ^0.4.4 | Linting e formatação de código |
| **Type Checker** | mypy | ^1.10.0 | Verificação estática de tipos |
| **Security** | Bandit | ^1.7.8 | Análise estática de segurança |
| **Testes** | pytest | ^7.4.4 | Testes unitários e de integração |
| **Testes E2E** | pytest-playwright | ^0.6.2 | Testes end-to-end em browser |
| **CI/CD** | GitHub Actions | — | Pipeline automatizado |

---

## 3. Estrutura de Pastas

```
toninho-processo-extracao/
├── toninho/                          # Código-fonte principal
│   ├── main.py                       # Setup da aplicação FastAPI
│   ├── api/                          # Camada de API
│   │   ├── routes/                   # Definição de rotas/endpoints
│   │   │   ├── health.py             # Health check (/health, /info)
│   │   │   ├── processos.py          # CRUD de processos
│   │   │   ├── execucoes.py          # Gerenciamento de execuções
│   │   │   ├── paginas_extraidas.py  # Páginas extraídas e downloads
│   │   │   ├── configuracoes.py      # Configurações de processos
│   │   │   ├── logs.py               # Logs e streaming SSE
│   │   │   └── monitoring.py         # Endpoints de monitoramento
│   │   ├── dependencies/             # Injeção de dependência (Depends)
│   │   │   ├── processo_deps.py
│   │   │   ├── execucao_deps.py
│   │   │   ├── pagina_extraida_deps.py
│   │   │   ├── configuracao_deps.py
│   │   │   └── log_deps.py
│   │   └── frontend.py              # Rotas de templates e arquivos estáticos
│   ├── core/                         # Configuração e infraestrutura
│   │   ├── config.py                 # Settings (pydantic-settings + .env)
│   │   ├── database.py               # Engine e sessão SQLAlchemy
│   │   ├── exceptions.py             # Exceções customizadas
│   │   ├── logging.py                # Configuração de Loguru
│   │   └── constants.py              # Constantes da aplicação
│   ├── models/                       # Modelos SQLAlchemy (ORM)
│   │   └── enums.py                  # Enumerações do domínio
│   ├── schemas/                      # Schemas Pydantic (DTOs)
│   │   └── responses.py              # Wrappers de resposta padrão
│   ├── repositories/                 # Camada de acesso a dados
│   ├── services/                     # Camada de lógica de negócio
│   ├── extraction/                   # Módulo de extração (autônomo)
│   │   ├── extractor.py              # PageExtractor — orquestrador principal
│   │   ├── http_client.py            # Cliente HTTP com retry, cache e rate limit
│   │   ├── browser_client.py         # Playwright: renderização de SPAs
│   │   ├── docling_extractor.py      # Extração via IBM Docling
│   │   ├── markdown_converter.py     # Pipeline HTML → Markdown + frontmatter
│   │   ├── storage.py                # Abstração de armazenamento (Strategy)
│   │   └── utils.py                  # Utilitários (sanitização, paths)
│   ├── workers/                      # Workers Celery
│   │   ├── celery_app.py             # Configuração do app Celery
│   │   ├── config.py                 # Configurações de worker e retry
│   │   ├── utils.py                  # ExtractionOrchestrator
│   │   └── tasks/                    # Tasks assíncronas
│   │       ├── execucao_task.py      # Task principal de extração
│   │       ├── agendamento_task.py   # Verificação de agendamentos (60s)
│   │       └── limpeza_task.py       # Limpeza de logs antigos (diária)
│   └── monitoring/                   # Monitoramento e métricas
├── frontend/                         # Assets do frontend (HTMX, Alpine.js, CSS)
├── tests/                            # Suíte de testes
├── migrations/                       # Migrações Alembic
├── scripts/                          # Scripts utilitários
├── docs/                             # Documentação
│   └── adr/                          # Architecture Decision Records
├── output/                           # Arquivos Markdown extraídos
├── logs/                             # Arquivos de log
├── docker-compose.yml                # Composição de serviços Docker
├── docker-compose.override.yml       # Overrides para desenvolvimento
├── Dockerfile                        # Imagem Docker da aplicação
├── entrypoint.sh                     # Script de inicialização do container
├── pyproject.toml                    # Dependências e configuração Poetry
├── alembic.ini                       # Configuração do Alembic
├── tailwind.config.js                # Configuração TailwindCSS
├── package.json                      # Dependências Node.js (TailwindCSS)
└── Makefile                          # Atalhos de comandos
```

---

## 4. Arquitetura em Camadas

### Diagrama

```
┌─────────────────────────────────────────────────┐
│                    FRONTEND                      │
│         HTMX + Alpine.js + Jinja2               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│              API LAYER (FastAPI)                 │
│  routes/ → Validação Pydantic → Depends()       │
└──────┬───────────────────────────────┬──────────┘
       │                               │
       ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  SERVICE LAYER   │          │  CELERY WORKERS  │
│  Lógica negócio  │          │  Tasks assíncr.  │
└──────┬───────────┘          └──────┬───────────┘
       │                               │
       ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│ REPOSITORY LAYER │          │ EXTRACTION MODULE│
│ SQLAlchemy ORM   │          │ HTTP / Playwright│
└──────┬───────────┘          │ HTML → Markdown  │
       │                      └──────────────────┘
       ▼
┌──────────────────┐
│    DATABASE       │
│ SQLite / Postgres │
└──────────────────┘
```

### Regras de Dependência

| Regra | Descrição |
|---|---|
| **Fluxo unidirecional** | API → Service → Repository → Model (nunca o inverso) |
| **Workers acessam Services** | Tasks Celery chamam a camada de serviço diretamente |
| **Extração autônoma** | O módulo `extraction/` não depende de outras camadas |
| **Injeção de dependência** | Toda dependência é injetada via `FastAPI Depends()` |
| **Schemas separados de Models** | Pydantic (schemas) para API, SQLAlchemy (models) para banco |

### Descrição das Camadas

- **Frontend**: Templates Jinja2 renderizados no servidor. HTMX para requisições parciais sem refresh. Alpine.js para estado local e interatividade mínima. TailwindCSS para estilização.
- **API Layer**: Rotas FastAPI que validam entrada com Pydantic, injetam dependências e delegam à camada de serviço. Não contém lógica de negócio.
- **Service Layer**: Regras de negócio, orquestração de operações, validações complexas e despacho de tasks Celery.
- **Repository Layer**: Acesso a dados via SQLAlchemy ORM. Encapsula queries e transações.
- **Extraction Module**: Módulo autônomo responsável por buscar HTML (via HTTP ou browser), converter para Markdown e persistir no armazenamento.
- **Workers**: Tasks Celery que executam processos de longa duração fora do ciclo request/response da API.

---

## 5. Entidades e Ciclo de Vida

Todas as enumerações estão definidas em `toninho/models/enums.py` e herdam de `str` + `enum.Enum` para compatibilidade com JSON e SQLAlchemy.

### 5.1. Processo (`ProcessoStatus`)

Representa um processo de extração configurado pelo usuário.

```
        ativar                   arquivar
  ┌──────────────┐        ┌──────────────────┐
  │              ▼        │                  ▼
INATIVO ◄────► ATIVO ────────────────► ARQUIVADO
         desativar
```

| Status | Valor | Descrição |
|---|---|---|
| `ATIVO` | `"ativo"` | Processo ativo e operacional |
| `INATIVO` | `"inativo"` | Desativado temporariamente |
| `ARQUIVADO` | `"arquivado"` | Arquivado (não aparece em listagens) |

### 5.2. Execução (`ExecucaoStatus`)

Representa uma execução individual de um processo de extração.

```
CRIADO → AGUARDANDO → EM_EXECUCAO ─┬─→ CONCLUIDO
                          │         ├─→ CONCLUIDO_COM_ERROS
                          │         ├─→ FALHOU
                          ▼         └─→ CANCELADO
                       PAUSADO
```

| Status | Valor | Descrição |
|---|---|---|
| `CRIADO` | `"criado"` | Execução criada, aguardando envio |
| `AGUARDANDO` | `"aguardando"` | Na fila, aguardando worker disponível |
| `EM_EXECUCAO` | `"em_execucao"` | Sendo processada por um worker |
| `PAUSADO` | `"pausado"` | Pausada manualmente pelo usuário |
| `CONCLUIDO` | `"concluido"` | Finalizada com sucesso total |
| `CONCLUIDO_COM_ERROS` | `"concluido_com_erros"` | Sucesso parcial (algumas páginas falharam) |
| `FALHOU` | `"falhou"` | Finalizada com erro total |
| `CANCELADO` | `"cancelado"` | Cancelada pelo usuário |

### 5.3. Página Extraída (`PaginaStatus`)

| Status | Valor | Descrição |
|---|---|---|
| `SUCESSO` | `"sucesso"` | Página extraída com sucesso |
| `FALHOU` | `"falhou"` | Falha na extração da página |
| `IGNORADO` | `"ignorado"` | Página ignorada (filtros, duplicada, etc.) |

### 5.4. Log (`LogNivel`)

| Nível | Valor |
|---|---|
| `DEBUG` | `"debug"` |
| `INFO` | `"info"` |
| `WARNING` | `"warning"` |
| `ERROR` | `"error"` |

### 5.5. Formato de Saída (`FormatoSaida`)

| Formato | Valor | Descrição |
|---|---|---|
| `ARQUIVO_UNICO` | `"arquivo_unico"` | Todas as páginas em um único arquivo Markdown |
| `MULTIPLOS_ARQUIVOS` | `"multiplos_arquivos"` | Uma página por arquivo Markdown |

### 5.6. Tipo de Agendamento (`AgendamentoTipo`)

| Tipo | Valor | Descrição |
|---|---|---|
| `RECORRENTE` | `"recorrente"` | Execução recorrente via expressão cron |
| `ONE_TIME` | `"one_time"` | Execução única em data/hora agendada |
| `MANUAL` | `"manual"` | Sem agendamento — execução disparada manualmente |

### 5.7. Método de Extração (`MetodoExtracao`)

| Método | Valor | Descrição |
|---|---|---|
| `HTML2TEXT` | `"html2text"` | BeautifulSoup + html2text (rápido, suporta SPA) |
| `DOCLING` | `"docling"` | IBM Docling — extração semântica estruturada (não suporta SPA) |

---

## 6. Métodos de Extração

O módulo `toninho/extraction/` é autônomo e implementa dois métodos de extração com dois modos de obtenção de HTML:

### Métodos

| Método | Tecnologia | Velocidade | SPA | Saída |
|---|---|---|---|---|
| **HTML2TEXT** | BeautifulSoup4 + html2text | ⚡ Rápido | ✅ (via Playwright) | Markdown limpo |
| **DOCLING** | IBM Docling | 🐢 Mais lento | ❌ | Markdown semântico estruturado |

### Modos de Obtenção de HTML

| Modo | Classe | Quando usar | Características |
|---|---|---|---|
| **HTTP** (padrão) | `HTTPClient` | Sites estáticos, APIs | Rápido, retry com backoff exponencial, cache em memória, rate limiting por domínio |
| **Browser** | `BrowserClient` | SPAs (React, Vue, Angular) | Playwright headless Chromium, espera por eventos configuráveis (`load`, `domcontentloaded`, `networkidle`, `commit`) |

### Pipeline de Conversão

```
URL
 │
 ├─ [HTTP mode] ──→ HTTPClient.fetch(url)
 │                    • Retry: 1s, 2s, 4s (backoff exponencial)
 │                    • Cache em memória (TTL configurável)
 │                    • Rate limiting por domínio
 │
 └─ [Browser mode] → BrowserClient.render(url)
                      • Chromium headless via Playwright
                      • Aguarda renderização JS completa
 │
 ▼
HTML bruto
 │
 ├─ [HTML2TEXT] ──→ MarkdownConverter
 │                    • Extrai <title> ou <h1>
 │                    • Converte HTML → Markdown (html2text)
 │                    • Limpa e normaliza conteúdo
 │                    • Adiciona frontmatter YAML (URL, título, timestamp)
 │
 └─ [DOCLING] ───→ DoclingExtractor
                     • Conversão semântica avançada
                     • Preserva tabelas e hierarquia
 │
 ▼
Markdown final → Storage (LocalFileSystem / futuro: S3)
```

### Armazenamento

O módulo usa o padrão **Strategy** para abstração de armazenamento:

- **`StorageInterface`**: Interface abstrata base.
- **`LocalFileSystemStorage`**: Implementação atual — grava em `./output/`.
- **S3/Cloud**: Preparado para extensão futura via factory.

---

## 7. Fluxo de Execução (Workflow Completo)

### Passo 1 — Criação via API

```
Cliente (HTMX / curl) ──→ POST /api/v1/execucoes/
                              │
                              ▼
                     FastAPI route (execucoes.py)
                              │
                              ▼
                     ExecucaoService.create_execucao()
                              │
                              ├─ Valida processo (ATIVO?)
                              ├─ Cria registro Execução (status: CRIADO)
                              ├─ Despacha Celery task → executar_processo_task.delay(execucao_id)
                              └─ Retorna HTTP 201 imediatamente
```

### Passo 2 — Processamento Assíncrono (Worker)

```
Redis Queue ──→ Celery Worker captura a task
                       │
                       ▼
              executar_processo_task(execucao_id)
                       │
                       ▼
              ExtractionOrchestrator.run(execucao_id)
                       │
                       ├─ Atualiza status: AGUARDANDO → EM_EXECUCAO
                       ├─ Busca configuração do processo (URLs, método, formato)
                       │
                       ├─ Para cada URL:
                       │     ├─ PageExtractor.extract(url, method, use_browser)
                       │     ├─ Salva PaginaExtraida (SUCESSO / FALHOU / IGNORADO)
                       │     └─ Registra Log de extração
                       │
                       ├─ Atualiza métricas (total, sucesso, falhas)
                       └─ Atualiza status final:
                             ├─ Todas OK ──→ CONCLUIDO
                             ├─ Algumas falharam ──→ CONCLUIDO_COM_ERROS
                             └─ Todas falharam ──→ FALHOU
```

### Passo 3 — Consulta de Resultados

```
Cliente ──→ GET /api/v1/execucoes/{id}
               │
               ▼
         Retorna execução com status, métricas e páginas extraídas

Cliente ──→ GET /api/v1/paginas-extraidas/?execucao_id={id}
               │
               ▼
         Lista páginas com conteúdo Markdown e metadados

Cliente ──→ GET /api/v1/paginas-extraidas/{id}/download
               │
               ▼
         Download do arquivo Markdown individual ou ZIP
```

### Tasks Periódicas (Celery Beat)

| Task | Intervalo | Descrição |
|---|---|---|
| `verificar_agendamentos` | A cada 60 segundos | Verifica processos com agendamento pendente e dispara execuções |
| `limpar_logs_antigos` | Diária | Remove logs com mais de 30 dias |

### Configuração de Retry

- **Máximo de tentativas**: 3
- **Estratégia**: Backoff exponencial
- **Hard time limit**: 2 horas por task
- **Prefetch multiplier**: 1 (uma task por vez por worker)

---

## 8. Infraestrutura Docker

### Serviços

```
┌──────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                         │
│                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────────┐  │
│  │  Redis   │   │   API   │   │ Worker  │   │   Beat    │  │
│  │  :6379   │◄──│  :8000  │   │ Celery  │   │  Celery   │  │
│  │  broker  │◄──│ FastAPI │   │ conc=2  │   │ scheduler │  │
│  └────┬─────┘   └────┬────┘   └────┬────┘   └─────┬─────┘  │
│       │              │              │               │        │
│       │              │         ┌────┴────┐          │        │
│       │              │         │ Flower  │          │        │
│       │              │         │  :5555  │          │        │
│       │              │         │ monitor │          │        │
│       │              │         └─────────┘          │        │
│       └──────────────┴──────────────────────────────┘        │
│                    toninho_network (bridge)                   │
└──────────────────────────────────────────────────────────────┘
```

### Detalhamento dos Serviços

| Serviço | Imagem / Build | Porta | Função | Dependências |
|---|---|---|---|---|
| **redis** | `redis:7-alpine` | `6379` | Message broker + result backend | — |
| **api** | Build local (`Dockerfile`) | `8000` | FastAPI + Uvicorn (ASGI) | redis (healthy) |
| **worker** | Build local (`Dockerfile`) | — | Celery worker (concurrency=2) | api (healthy) |
| **beat** | Build local (`Dockerfile`) | — | Celery Beat — agendador de tasks | api (healthy) |
| **flower** | Build local (`Dockerfile`) | `5555` | Dashboard de monitoramento Celery | api (healthy) |

### Volumes

| Volume | Tipo | Descrição |
|---|---|---|
| `redis_data` | Named volume | Persistência dos dados Redis |
| `db_data` | Named volume | Persistência do banco de dados |
| `./output` | Bind mount | Arquivos Markdown extraídos |

### Rede

Todos os serviços compartilham a rede `toninho_network` (driver: bridge), permitindo comunicação interna via nome do serviço.

---

## 9. Formato de Resposta da API

Todas as respostas da API seguem um formato padronizado definido em `toninho/schemas/responses.py`.

### Resposta de Sucesso (Item Único)

```json
{
  "success": true,
  "data": {
    "id": "uuid-do-recurso",
    "nome": "Meu Processo",
    "status": "ativo",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Resposta de Sucesso (Lista Paginada)

```json
{
  "data": [
    { "id": "uuid-1", "nome": "Processo A" },
    { "id": "uuid-2", "nome": "Processo B" }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Resposta de Erro

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Processo não encontrado",
    "details": [
      { "field": "id", "message": "Nenhum processo com o ID informado" }
    ]
  }
}
```

### Códigos de Erro Comuns

| Código | HTTP Status | Descrição |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Dados de entrada inválidos |
| `NOT_FOUND` | 404 | Recurso não encontrado |
| `CONFLICT` | 409 | Conflito de estado (ex: processo já arquivado) |
| `INTERNAL_ERROR` | 500 | Erro interno do servidor |

### Helpers

O módulo `responses.py` fornece funções utilitárias para construção padronizada:

- **`success_response(data)`** — Encapsula um item em `SuccessResponse[T]`.
- **`success_list_response(data, meta)`** — Encapsula uma lista em `SuccessListResponse[T]` com metadados de paginação.
- **`error_response(code, message, details)`** — Encapsula um erro em `ErrorResponse`.

---

## 10. Referências

### Architecture Decision Records (ADRs)

| ADR | Título | Descrição |
|---|---|---|
| [ADR-001](adr/ADR-001-stack-tecnologico.md) | Stack Tecnológico Principal | Escolha de FastAPI, SQLAlchemy 2.x, Pydantic v2, Celery + Redis, PostgreSQL |
| [ADR-002](adr/ADR-002-processamento-assincrono.md) | Processamento Assíncrono via Celery | Justificativa da escolha de Celery sobre asyncio, BackgroundTasks, RQ e APScheduler |
| [ADR-003](adr/ADR-003-banco-de-dados.md) | Estratégia de Banco de Dados | SQLite para desenvolvimento, PostgreSQL para produção |
| [ADR-004](adr/ADR-004-arquitetura-camadas.md) | Arquitetura em Camadas | Separação em routes, services, repositories e models |
| [ADR-005](adr/ADR-005-modulo-extracao.md) | Módulo de Extração | Design do módulo com httpx + BeautifulSoup + html2text |
| [ADR-006](adr/ADR-006-frontend.md) | Frontend HTMX + Alpine.js | Escolha de HTMX + Alpine.js + TailwindCSS sobre frameworks SPA |
| [ADR-007](adr/ADR-007-qualidade-software.md) | Qualidade de Software | Padrões de qualidade, testes e ferramentas de análise |

### Links Úteis

- **FastAPI**: https://fastapi.tiangolo.com/
- **Celery**: https://docs.celeryq.dev/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **HTMX**: https://htmx.org/
- **Alpine.js**: https://alpinejs.dev/
- **Docling (IBM)**: https://github.com/DS4SD/docling
- **Playwright**: https://playwright.dev/python/
