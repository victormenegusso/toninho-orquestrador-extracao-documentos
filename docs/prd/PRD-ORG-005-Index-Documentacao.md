# PRD-ORG-005: Índice de Documentação

**Status**: ✅ Implementado
**Prioridade**: 🟡 Baixa
**Categoria**: Documentação
**Tipo**: Novo Documento

---

## 1. Objetivo

Criar o arquivo `docs/README.md` como índice de navegação de toda a documentação do projeto, organizado por categoria, para que humanos e IAs encontrem rapidamente o documento relevante.

## 2. Contexto e Justificativa

A pasta `docs/` contém 48+ arquivos Markdown em múltiplas subpastas (adr/, prd/, discoverys/, demandas/, diagramas/). Não existe um índice que guie a navegação.

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: D5
- **Dependências**: PRD-ORG-002, PRD-ORG-003, PRD-ORG-004 (deve ser executado após)

---

## 3. Conteúdo Obrigatório

### 3.1. Título e Descrição

```markdown
# 📚 Documentação do Projeto Toninho

Índice de navegação para toda a documentação do projeto.
```

### 3.2. Documentação Principal

Links para os documentos de alto nível:

| Documento | Descrição |
|-----------|-----------|
| [Arquitetura](ARCHITECTURE.md) | Visão completa: estrutura, camadas, entidades, fluxos |
| [API](API.md) | Referência dos endpoints REST |
| [Testes](TESTING.md) | Guia de testes e cobertura E2E |
| [Como Usar](como-usar.md) | Tutorial passo-a-passo da API |

### 3.3. ADRs (Architecture Decision Records)

Tabela com todos os ADRs:

| ADR | Título | Status |
|-----|--------|--------|
| [ADR-001](adr/ADR-001-stack-tecnologico.md) | Stack Tecnológico | Aceito |
| [ADR-002](adr/ADR-002-processamento-assincrono.md) | Processamento Assíncrono | Aceito |
| ... | ... | ... |

### 3.4. PRDs (Product Requirements Documents)

Tabela com todos os PRDs organizados por categoria:

**Fundação:**
| PRD | Título | Status |
|-----|--------|--------|
| [PRD-001](prd/PRD-001-Setup-Projeto.md) | Setup do Projeto | ✅ Implementado |
| ... | ... | ... |

**Backend Core:**
| PRD | Título | Status |
|-----|--------|--------|

**Frontend:**
| PRD | Título | Status |

**E2E Playwright:**
| PRD | Título | Status |

**Organização (novos):**
| PRD | Título | Status |

**Tech Debt:**
| PRD | Título | Status |

### 3.5. Discoverys

Lista de documentos de discovery:

| Discovery | Descrição |
|-----------|-----------|
| [Base](discoverys/base/inicio-projeto.md) | Início do projeto |
| [E2E Frontend](discoverys/e2e-front/inicio-notas.md) | Testes de frontend com Playwright |
| [Organização v2](discoverys/organizacao-projeto-v2/discovery.md) | Reorganização do projeto |

### 3.6. Demandas e Backlog

| Documento | Descrição |
|-----------|-----------|
| [Backlog](demandas/backlog.md) | Bugs, melhorias e tech debt |
| [Deploy VPS](demandas/deploy-vps.md) | Notas sobre deploy |
| [Extração Docling](demandas/extracao-docling.md) | Integração IBM Docling |

### 3.7. Diagramas

| Documento | Descrição |
|-----------|-----------|
| [Fluxo de Extração](diagramas/arquitetura-fluxo-extracao.md) | Diagrama Mermaid do fluxo |

---

## 4. Critérios de Aceite

- [ ] Arquivo `docs/README.md` criado
- [ ] Todos os arquivos .md em docs/ estão referenciados
- [ ] Links relativos corretos (verificar que paths existem)
- [ ] Organizado por categoria (Principal, ADRs, PRDs, Discoverys, Demandas)
- [ ] PRDs com status (Implementado/Planejado)
- [ ] Documento em Português (PT-BR)

---

## 5. Fontes de Informação

O agente deve:
- Executar `find docs/ -name "*.md" -type f | sort` para listar todos os arquivos
- Ler a primeira linha de cada arquivo para extrair o título
- Verificar se os links relativos estão corretos
