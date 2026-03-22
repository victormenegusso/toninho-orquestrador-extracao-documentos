# 📚 Documentação do Projeto Toninho

Índice de navegação para toda a documentação do projeto.

---

## 📋 Documentação Principal

| Documento | Descrição |
|-----------|-----------|
| [Arquitetura](ARCHITECTURE.md) | Visão completa: estrutura de pastas, camadas, entidades, fluxos e stack |
| [API](API.md) | Referência completa dos 47 endpoints REST |
| [Testes](TESTING.md) | Guia de testes: unit, integration, E2E + mapeamento de cobertura |
| [Como Usar](como-usar.md) | Tutorial passo-a-passo da API |

---

## 🏛️ ADRs (Architecture Decision Records)

| ADR | Título | Status |
|-----|--------|--------|
| [ADR-001](adr/ADR-001-stack-tecnologico.md) | Stack Tecnológico Principal | Aceito |
| [ADR-002](adr/ADR-002-processamento-assincrono.md) | Processamento Assíncrono via Celery | Aceito |
| [ADR-003](adr/ADR-003-banco-de-dados.md) | Estratégia de Banco de Dados | Aceito |
| [ADR-004](adr/ADR-004-arquitetura-camadas.md) | Arquitetura em Camadas | Aceito |
| [ADR-005](adr/ADR-005-modulo-extracao.md) | Módulo de Extração (httpx + BeautifulSoup + html2text) | Aceito |
| [ADR-006](adr/ADR-006-frontend.md) | Frontend HTMX + Alpine.js | Aceito |
| [ADR-007](adr/ADR-007-qualidade-software.md) | Qualidade de Software — Ferramentas e Padrões | Aceito |

---

## 📄 PRDs (Product Requirements Documents)

### Fundação

| PRD | Título | Status |
|-----|--------|--------|
| [PRD-001](prd/PRD-001-Setup-Projeto.md) | Setup do Projeto | ✅ Implementado |
| [PRD-002](prd/PRD-002-Ambiente-Desenvolvimento.md) | Ambiente de Desenvolvimento | ✅ Implementado |
| [PRD-003](prd/PRD-003-Models-Database.md) | Models e Database | ✅ Implementado |
| [PRD-004](prd/PRD-004-Schemas-DTOs.md) | Schemas e DTOs | ✅ Implementado |

### Backend Core

| PRD | Título | Status |
|-----|--------|--------|
| [PRD-005](prd/PRD-005-Modulo-Processo.md) | Módulo Processo | ✅ Implementado |
| [PRD-006](prd/PRD-006-Modulo-Configuracao.md) | Módulo Configuração | ✅ Concluído |
| [PRD-007](prd/PRD-007-Modulo-Execucao.md) | Módulo Execução | ✅ Concluído |
| [PRD-008](prd/PRD-008-Modulo-Log.md) | Módulo Log | ✅ Concluído |
| [PRD-009](prd/PRD-009-Modulo-Pagina-Extraida.md) | Módulo Página Extraída | ✅ Concluído |
| [PRD-010](prd/PRD-010-Workers-Processamento-Assincrono.md) | Workers e Processamento Assíncrono | ✅ Concluído |
| [PRD-011](prd/PRD-011-Sistema-Extracao.md) | Sistema de Extração | ✅ Concluído |
| [PRD-012](prd/PRD-012-Monitoramento-Metricas.md) | Monitoramento e Métricas | ✅ Concluído |
| [PRD-013](prd/PRD-013-Testes-Qualidade.md) | Testes e Qualidade | ✅ Concluído |
| [PRD-018](prd/PRD-018-Integracao-Docling.md) | Integração Docling | 📋 Planejado |

### Frontend

| PRD | Título | Status |
|-----|--------|--------|
| [PRD-014](prd/PRD-014-Setup-Frontend.md) | Setup Frontend | ✅ Concluído |
| [PRD-015](prd/PRD-015-Interface-CRUD-Processos.md) | Interface CRUD Processos | ✅ Concluído |
| [PRD-016](prd/PRD-016-Interface-Monitoramento.md) | Interface de Monitoramento | ✅ Concluído |
| [PRD-017](prd/PRD-017-Detalhes-Downloads.md) | Detalhes e Downloads | ✅ Concluído |

### E2E Playwright

| PRD | Título | Status |
|-----|--------|--------|
| [PRD-019](prd/PRD-019-implementacao-playwright-setup-infraestrutura.md) | Setup de Infraestrutura E2E | 📋 Planejado |
| [PRD-020](prd/PRD-020-implementacao-playwright-crud-processos.md) | CRUD de Processos | 📋 Planejado |
| [PRD-021](prd/PRD-021-implementacao-playwright-listagem-busca-processos.md) | Listagem, Busca e Ações em Processos | 📋 Planejado |
| [PRD-022](prd/PRD-022-implementacao-playwright-dashboard-polling.md) | Dashboard com Polling Automático | 📋 Planejado |
| [PRD-023](prd/PRD-023-implementacao-playwright-execucoes-ciclo-vida.md) | Execuções: Ciclo de Vida e Listagem | 📋 Planejado |
| [PRD-024](prd/PRD-024-implementacao-playwright-logs-sse-tempo-real.md) | Logs em Tempo Real via SSE | 📋 Planejado |
| [PRD-025](prd/PRD-025-implementacao-playwright-paginas-notificacoes-navegacao.md) | Páginas Extraídas, Notificações e Navegação | 📋 Planejado |

### Organização

| PRD | Título | Status |
|-----|--------|--------|
| [PRD-ORG-001](prd/PRD-ORG-001-Atualizacao-README.md) | Atualização do README.md | ✅ Implementado |
| [PRD-ORG-002](prd/PRD-ORG-002-Documento-Arquitetura.md) | Documento de Arquitetura | ✅ Implementado |
| [PRD-ORG-003](prd/PRD-ORG-003-Documento-API.md) | Documento da API | ✅ Implementado |
| [PRD-ORG-004](prd/PRD-ORG-004-Documento-Testes.md) | Documento de Testes | ✅ Implementado |
| [PRD-ORG-005](prd/PRD-ORG-005-Index-Documentacao.md) | Índice de Documentação | ✅ Implementado |
| [PRD-ORG-006](prd/PRD-ORG-006-Otimizacao-Docker.md) | Otimização Docker Build | ✅ Implementado |
| [PRD-ORG-007](prd/PRD-ORG-007-Teste-E2E-Formularios.md) | Teste E2E Anti-Regressão de Formulários | ✅ Implementado |
| [PRD-ORG-008](prd/PRD-ORG-008-Atualizacao-Backlog.md) | Atualização do Backlog | ✅ Implementado |

### Tech Debt

| PRD | Título | Status |
|-----|--------|--------|
| [PRD-DT-001](prd/PRD-DT-001-Correcao-Warnings-Deprecados.md) | Correção de Warnings Deprecados | ✅ Implementado |

### Prompts e Implementação

| Documento | Descrição |
|-----------|-----------|
| [Plano PRD-018](prd/impl-prd-018.md) | Plano de implementação — Integração Docling |
| [Prompt PRD-018](prd/prompts/impl-prd-018.prompt.md) | Prompt de implementação — Docling |
| [Prompt PRDs 019-025](prd/prompts/impl-prds-019-025-playwright-e2e.md) | Prompt de implementação — Testes E2E Playwright |

---

## 🔍 Discoverys

| Discovery | Descrição |
|-----------|-----------|
| [Início do Projeto](discoverys/base/inicio-projeto.md) | Definição inicial do projeto Toninho |
| [Perguntas de Enriquecimento](discoverys/base/pergunta-1.md) | Perguntas para enriquecimento do projeto |
| [Testes E2E Frontend](discoverys/e2e-front/inicio-notas.md) | Discovery de testes de frontend com Playwright |
| [Casos de Uso E2E](discoverys/e2e-front/casos_de_uso_e2e.md) | Definição dos casos de uso E2E |
| [Prompt E2E p1](discoverys/e2e-front/prompts/p1.md) | Prompt para análise de casos de uso E2E |
| [Prompt E2E p2](discoverys/e2e-front/prompts/p2.md) | Prompt para geração de PRDs E2E |
| [Organização v1.1](discoverys/organizacao-projeto-v1-1/notasV1.md) | Notas da primeira tentativa de organização |
| [Organização v2](discoverys/organizacao-projeto-v2/discovery.md) | Discovery completo da reorganização do projeto |
| [Prompt Execução PRDs](discoverys/organizacao-projeto-v2/prompt-execucao-prds.md) | Prompt para execução dos PRDs de organização |

---

## 📦 Demandas e Backlog

| Documento | Descrição |
|-----------|-----------|
| [Backlog](demandas/backlog.md) | Bugs, melhorias e tech debt pendentes |
| [Deploy VPS](demandas/deploy-vps.md) | Notas sobre deploy em VPS |
| [Extração Docling](demandas/extracao-docling.md) | Descrição da integração IBM Docling |

---

## 📊 Diagramas

| Documento | Descrição |
|-----------|-----------|
| [Fluxo de Extração](diagramas/arquitetura-fluxo-extracao.md) | Diagrama Mermaid do fluxo de extração |
