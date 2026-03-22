# Discovery: Organização do Projeto Toninho v2

**Projeto Toninho — Sistema de Extração de Documentos**
*Versão 2.0 · Março 2026*

---

## 1. Descrição do Discovery

Este discovery mapeia o estado atual do projeto Toninho e identifica pontos de melhoria na **organização da documentação, configuração Docker e cobertura de testes de frontend**. O objetivo é gerar PRDs acionáveis para que agentes de IA possam executar as correções de forma autônoma, sem ambiguidade.

### Escopo

- ✅ Documentação (README, docs de arquitetura, docs de API, docs de testes)
- ✅ Configuração Docker (build time, otimizações)
- ✅ Cobertura de testes E2E (bugs recorrentes de frontend)
- ✅ Backlog (atualização e validação)
- ❌ Estrutura de pastas do código (`toninho/`) — já está bem organizada
- ❌ Alterações de funcionalidade ou lógica de negócio

### Motivação

O desenvolvedor (solo + IA) enfrenta três dores:

1. **Documentação desatualizada** — o README referencia ferramentas e diretórios que não existem, e falta documentação de arquitetura que reflita a realidade do projeto
2. **Docker lento** — o `docker compose up --build` constrói a mesma imagem 4 vezes (api, worker, beat, flower)
3. **Bugs recorrentes no frontend** — regressões em campos pré-preenchidos e estados HTMX/Alpine.js que voltam após mudanças no código

---

## 2. Objetivo do Discovery

Produzir um mapeamento completo e validado dos problemas, para que os PRDs gerados a partir deste documento sejam:

- **Atômicos** — cada PRD resolve um problema isolado
- **Executáveis por IA** — com contexto suficiente para um agente implementar sem perguntas
- **Testáveis** — com critérios de aceite claros e verificáveis
- **Sem efeitos colaterais** — nenhum PRD altera funcionalidade existente

---

## 3. Análise do Estado Atual

### 3.1 Estrutura de Pastas

```
toninho-processo-extracao/
├── toninho/              ✅ Bem organizado (API → Services → Repositories → Models)
├── frontend/             ✅ Templates + Static separados
├── tests/                ✅ Unit + Integration + E2E (Playwright)
├── migrations/           ✅ Alembic com naming temporal
├── scripts/              ✅ Scripts utilitários
├── docs/                 ⚠️  Precisa de reorganização (detalhado abaixo)
├── Dockerfile            ⚠️  Funcional mas com oportunidade de otimização
├── docker-compose.yml    ⚠️  Build redundante (4x mesma imagem)
├── README.md             🔴 Desatualizado (ferramentas e links incorretos)
└── pyproject.toml        ✅ Correto e completo
```

### 3.2 Documentação — Problemas Identificados

#### 3.2.1 README.md — Desatualizado

| Linha | Problema | Estado Real |
|-------|---------|-------------|
| 126-130 | Menciona "Black e isort para formatação" | Projeto usa **Ruff** (linter + formatter) |
| 157 | Lista "black, isort, flake8, mypy" como Quality tools | Correto é **ruff, mypy, bandit** |
| 164 | Link para `docs/architecture/` | Diretório **não existe**; existe `docs/diagramas/` |
| 165 | Link para `docs/api/` | Diretório **não existe** |
| 102-104 | Seção "API Endpoints" lista apenas 4 endpoints | Projeto tem **20+ endpoints** |
| 109-120 | Seção de testes não menciona E2E/Playwright | Testes E2E existem com 13 suítes |

#### 3.2.2 Falta Documento de Arquitetura Real

O projeto tem `docs/diagramas/arquitetura-fluxo-extracao.md` (apenas um Mermaid flowchart), mas **não tem** um documento completo de arquitetura que cubra:

- Estrutura de pastas com descrição de cada módulo
- Diagrama de arquitetura em camadas (API → Services → Repositories → Models)
- Ciclo de vida das entidades (Processo, Configuração, Execução, PáginaExtraída)
- Fluxo de execução assíncrona (Celery → Worker → Extraction)
- Comportamentos do sistema (SSE, WebSocket, polling, agendamento)
- Stack tecnológica com versões atuais

#### 3.2.3 Falta Documento de API

O README linka `docs/api/` que não existe. O projeto tem Swagger auto-gerado em `/docs`, mas falta uma documentação de referência em Markdown que:

- Liste todos os endpoints com método, path, descrição
- Documente os formatos de request/response
- Descreva os códigos de erro e suas causas
- Mapeie o fluxo de uso (3 passos: Processo → Configuração → Execução)

#### 3.2.4 Falta Documento de Testes E2E

Os testes E2E Playwright cobrem 13 casos de uso, mas não existe documentação que:

- Liste os UCs cobertos e o que cada teste valida
- Descreva como rodar os testes localmente
- Mapeie quais testes cobrem quais funcionalidades do frontend
- Sirva de referência para identificar gaps de cobertura

#### 3.2.5 Falta Index de Navegação na pasta docs/

Com 48 arquivos Markdown, a pasta `docs/` não tem um README.md ou index que guie o leitor (humano ou IA) sobre como navegar a documentação.

#### 3.2.6 Backlog Potencialmente Desatualizado

O arquivo `docs/demandas/backlog.md` (gerado em 2026-03-04) contém items que **já foram implementados**:

| Item | Status | Evidência |
|------|--------|-----------|
| MH-003 (Suporte JS/SPAs via Playwright) | ✅ **Implementado** | PRD-018, campo `use_browser` no modelo, `browser_client.py` existe |
| MH-004 (Endpoint cancelar execução) | **Verificar** | Endpoint pode existir mas não está no backlog como resolvido |
| TD-004 (healthcheck Docker API) | ✅ **Implementado** | `docker-compose.yml` linha 40-44 já tem healthcheck |
| BUG-001 (Task agendamento) | **Verificar** | Pode ter sido corrigido mas não está marcado |

---

### 3.3 Docker — Problemas Identificados

#### 3.3.1 Build Redundante (4 serviços × 1 imagem)

O `docker-compose.yml` define 4 serviços que fazem `build:` do mesmo `Dockerfile`:

```yaml
# api, worker, beat, flower — TODOS fazem:
build:
  context: .
  dockerfile: Dockerfile
```

**Impacto**: Sem cache efetivo, o Docker Compose constrói a imagem **4 vezes**. Mesmo com cache, cada serviço verifica os layers independentemente.

**Solução**: Definir a imagem uma vez e referenciar nos demais serviços:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: toninho:latest   # ← nomear a imagem

  worker:
    image: toninho:latest   # ← reusar (sem build)
    depends_on: [api]       # ← garante que a imagem existe
```

#### 3.3.2 Docling Cache Ausente no Compose Principal

O volume `docling_cache` está definido **apenas** no `docker-compose.override.yml` (dev), não no `docker-compose.yml` (produção). Em produção, o cache do Docling é perdido a cada restart.

---

### 3.4 Frontend — Bugs Recorrentes

#### 3.4.1 Problema Identificado

Campos pré-preenchidos em formulários (ex: página de criar processo) não carregam no primeiro acesso, apenas após reload. Esse bug já foi corrigido antes mas **regrediu**.

**Causa provável**: Estado Alpine.js (`x-data`) que depende de dados injetados pelo Jinja2 no template. Quando o HTMX faz swap parcial de DOM, o Alpine pode não re-inicializar.

**Solução recomendada**: Adicionar teste E2E específico que:
1. Navega direto para a página de criar processo (sem reload)
2. Verifica que todos os campos têm os valores default esperados
3. Testa navegação via HTMX (sidebar → criar processo) e valida os mesmos campos

Este teste deve ser adicionado como extensão do `test_uc01_criar_processo.py` ou como UC separado.

---

## 4. Passos para Organizar o Projeto

### 4.1 Documentação — O que devemos fazer

| # | Ação | Prioridade | Descrição |
|---|------|-----------|-----------|
| D1 | Atualizar README.md | 🔴 Alta | Corrigir referências a Black/isort/flake8 → Ruff. Corrigir links para docs. Simplificar: o README deve ser direto ao ponto com link para doc de arquitetura. Listar apenas os endpoints principais e linkar para doc completa. |
| D2 | Criar `docs/ARCHITECTURE.md` | 🔴 Alta | Documento completo de arquitetura: estrutura de pastas, diagrama de camadas, ciclo de vida das entidades, fluxo de execução, stack tecnológica, comportamentos (SSE, WebSocket, agendamento). |
| D3 | Criar `docs/API.md` | 🟠 Média | Referência da API REST: todos os endpoints, request/response, códigos de erro, fluxo de uso (3 passos). Gerado a partir do código + Swagger. |
| D4 | Criar `docs/TESTING.md` | 🟠 Média | Guia de testes: como rodar, UCs E2E cobertos, mapeamento de cobertura frontend, como adicionar novos testes. |
| D5 | Criar `docs/README.md` (index) | 🟡 Baixa | Índice de navegação da pasta docs. Lista todos os documentos organizados por categoria (ADRs, PRDs, Guides). |
| D6 | Atualizar `docs/demandas/backlog.md` | 🟡 Baixa | Marcar items já implementados (MH-003, TD-004). Verificar BUG-001 e MH-004. Adicionar novos items identificados. |

### 4.2 Docker — O que devemos fazer

| # | Ação | Prioridade | Descrição |
|---|------|-----------|-----------|
| K1 | Otimizar build: imagem compartilhada | 🔴 Alta | Definir `image: toninho:latest` no serviço `api` (que faz o build) e referenciar nos demais (worker, beat, flower) sem `build:`. Reduz tempo de build de ~4x para ~1x. |
| K2 | Adicionar Docling cache ao compose principal | 🟢 Baixa | Mover volume `docling_cache` do override para o `docker-compose.yml` principal. |

### 4.3 Testes — O que devemos fazer

| # | Ação | Prioridade | Descrição |
|---|------|-----------|-----------|
| T1 | Teste E2E: campos pré-preenchidos | 🔴 Alta | Criar teste que navega para formulário de criar processo via HTMX (sem reload) e valida que campos default estão preenchidos. Previne regressão do bug relatado. |
| T2 | Revisar cobertura E2E existente | 🟡 Baixa | Mapear quais funcionalidades do frontend não têm cobertura E2E e documentar gaps no TESTING.md. |

### 4.4 Configuração — O que devemos fazer

| # | Ação | Prioridade | Descrição |
|---|------|-----------|-----------|
| C1 | Nenhuma alteração necessária | ✅ | `pyproject.toml`, `alembic.ini`, `.pre-commit-config.yaml`, `.env.example` estão corretos e consistentes. |

### 4.5 Código — O que devemos fazer

| # | Ação | Prioridade | Descrição |
|---|------|-----------|-----------|
| X1 | Nenhuma alteração no escopo deste discovery | ✅ | A estrutura `toninho/` está bem organizada. Melhorias de código (tech debt, bugs do backlog) devem ser tratadas em discovery/PRDs separados. |

---

## 5. Padrão de Idioma

Conforme definido pelo desenvolvedor:

| Contexto | Idioma |
|----------|--------|
| Documentação (docs, README, PRDs, ADRs) | **Português (PT-BR)** |
| Código fonte (variáveis, funções, classes) | **Inglês (EN)** |
| Comentários no código | **Inglês (EN)** |
| Commit messages | **Inglês (EN)** — Conventional Commits |
| Nomes de arquivos de código | **Inglês (EN)** |
| Nomes de arquivos de docs | **Português (PT-BR)** permitido |

---

## 6. PRDs a Serem Gerados

Após aprovação deste discovery, os seguintes PRDs devem ser criados:

### PRD-ORG-001: Atualização do README.md
- **Escopo**: Corrigir informações incorretas, simplificar conteúdo, adicionar links para docs de arquitetura e API
- **Items cobertos**: D1
- **Dependências**: Nenhuma (pode ser executado primeiro)

### PRD-ORG-002: Documento de Arquitetura (`docs/ARCHITECTURE.md`)
- **Escopo**: Criar documento completo de arquitetura baseado no estado real do código
- **Items cobertos**: D2
- **Dependências**: Nenhuma

### PRD-ORG-003: Documento da API (`docs/API.md`)
- **Escopo**: Criar referência completa dos endpoints REST
- **Items cobertos**: D3
- **Dependências**: Nenhuma

### PRD-ORG-004: Documento de Testes (`docs/TESTING.md`)
- **Escopo**: Criar guia de testes com mapeamento de cobertura E2E
- **Items cobertos**: D4, T2
- **Dependências**: Nenhuma

### PRD-ORG-005: Index de Documentação (`docs/README.md`)
- **Escopo**: Criar índice de navegação da pasta docs
- **Items cobertos**: D5
- **Dependências**: PRD-ORG-002, PRD-ORG-003, PRD-ORG-004 (precisa saber quais docs existem)

### PRD-ORG-006: Otimização Docker Build
- **Escopo**: Configurar imagem compartilhada no docker-compose, adicionar Docling cache
- **Items cobertos**: K1, K2
- **Dependências**: Nenhuma

### PRD-ORG-007: Teste E2E Anti-Regressão de Formulários
- **Escopo**: Criar teste Playwright para campos pré-preenchidos e navegação HTMX
- **Items cobertos**: T1
- **Dependências**: Nenhuma

### PRD-ORG-008: Atualização do Backlog
- **Escopo**: Validar items do backlog, marcar implementados, adicionar novos
- **Items cobertos**: D6
- **Dependências**: Nenhuma (mas ideal executar por último como verificação)

---

## 7. Ordem de Execução Recomendada

```
Fase 1 (Paralelo — sem dependências):
  ├── PRD-ORG-001 (README)
  ├── PRD-ORG-002 (Arquitetura)
  ├── PRD-ORG-003 (API)
  ├── PRD-ORG-004 (Testes)
  ├── PRD-ORG-006 (Docker)
  └── PRD-ORG-007 (Teste E2E)

Fase 2 (Depende da Fase 1):
  └── PRD-ORG-005 (Index docs)

Fase 3 (Verificação):
  └── PRD-ORG-008 (Backlog)
```

---

## 8. Resultados Esperados

Após execução de todos os PRDs:

1. **README.md** — direto ao ponto, sem informações incorretas, com links para docs reais
2. **ARCHITECTURE.md** — documento vivo que reflete a estrutura, entidades, fluxos e stack do projeto
3. **API.md** — referência completa para desenvolvedores e IAs
4. **TESTING.md** — guia de testes com mapeamento de cobertura
5. **docs/README.md** — index de navegação com 48+ documentos organizados
6. **Docker build ~4x mais rápido** — imagem construída uma vez e compartilhada
7. **Teste E2E** — prevenção de regressão em campos pré-preenchidos
8. **Backlog atualizado** — refletindo o estado real do projeto

---

## 9. Conclusão

O projeto Toninho está **muito bem estruturado no código** — a arquitetura em camadas, testes, CI/CD e práticas de qualidade são sólidas. O gap principal está na **documentação de alto nível** (README, arquitetura, API) que não acompanhou a evolução do código.

Os 8 PRDs propostos são **cirúrgicos e independentes** (6 podem rodar em paralelo), focados em documentação e otimização — nenhum altera lógica de negócio ou estrutura de código. Isso minimiza risco e maximiza o impacto na compreensão do projeto por humanos e IAs.

---

## 10. Referências

- `README.md` — estado atual
- `docs/adr/` — ADR-001 a ADR-007
- `docs/prd/` — PRD-001 a PRD-025
- `docs/demandas/backlog.md` — backlog existente
- `docs/diagramas/arquitetura-fluxo-extracao.md` — diagrama Mermaid
- `docs/como-usar.md` — guia de uso da API
- `Dockerfile`, `docker-compose.yml`, `docker-compose.override.yml` — setup Docker
- `pyproject.toml` — dependências e configuração de ferramentas
- `tests/e2e/` — 13 suítes E2E Playwright existentes
