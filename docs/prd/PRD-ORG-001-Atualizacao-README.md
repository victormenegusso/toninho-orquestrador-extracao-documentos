# PRD-ORG-001: Atualização do README.md

**Status**: ✅ Implementado
**Prioridade**: 🔴 Alta
**Categoria**: Documentação
**Tipo**: Melhoria

---

## 1. Objetivo

Atualizar o `README.md` na raiz do projeto para refletir o estado real do projeto, corrigindo informações incorretas e simplificando o conteúdo com links para documentação detalhada.

## 2. Contexto e Justificativa

O README atual contém informações incorretas e desatualizadas:

| Problema | Local | Detalhe |
|----------|-------|---------|
| Ferramentas incorretas | Seção "Formatação de Código" | Menciona "Black e isort" — projeto usa **Ruff** |
| Stack incorreta | Seção "Tecnologias" | Lista "black, isort, flake8" — correto é **ruff, mypy, bandit** |
| Link quebrado | Seção "Documentação" | Link para `docs/architecture/` — diretório **não existe** |
| Link quebrado | Seção "Documentação" | Link para `docs/api/` — diretório **não existe** |
| API incompleta | Seção "API Endpoints" | Lista 4 endpoints — projeto tem **20+** |
| Testes incompletos | Seção "Testes" | Não menciona E2E/Playwright |

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: D1

---

## 3. Requisitos

### 3.1. Estrutura do Novo README

O README deve ser **direto ao ponto** — um resumo executivo com links para docs detalhadas. Estrutura:

```markdown
# Toninho - Sistema de Extração de Documentos
> Breve descrição (1-2 frases)

## Características (manter lista atual)

## Pré-requisitos (manter como está)

## Instalação Rápida
  - Local (simplificado)
  - Docker (simplificado)

## Uso
  - Comandos Make (manter)
  - Endpoints principais (apenas 5-6 principais + link para docs/API.md)

## Testes
  - Como rodar testes unitários/integração
  - Como rodar testes E2E (Playwright)
  - Link para docs/TESTING.md

## Tecnologias (CORRIGIR)

## Documentação (CORRIGIR links)
  - Link para docs/ARCHITECTURE.md
  - Link para docs/API.md
  - Link para docs/TESTING.md
  - Link para docs/README.md (index)
  - PRDs, ADRs

## Contribuindo (manter)

## Licença (manter)
```

### 3.2. Correções Obrigatórias

#### 3.2.1. Seção "Formatação de Código" (linhas 126-130)

**Antes:**
```markdown
### Formatação de Código

O projeto usa Black e isort para formatação:
```

**Depois:**
```markdown
### Formatação de Código

O projeto usa Ruff para linting e formatação:

\```bash
make format    # Auto-formata código
make lint      # Verifica linting e tipagem (ruff + mypy)
\```
```

#### 3.2.2. Seção "Tecnologias" (linha 157)

**Antes:**
```markdown
- **Quality**: black, isort, flake8, mypy
```

**Depois:**
```markdown
- **Quality**: ruff (linter + formatter), mypy (type checker), bandit (security)
```

#### 3.2.3. Seção "Documentação" (linhas 163-166)

**Antes:**
```markdown
- [PRDs](docs/prd/) - Product Requirements Documents
- [Arquitetura](docs/architecture/) - Diagramas
- [ADRs](docs/adr/) - Architecture Decision Records
- [API](docs/api/) - Documentação da API
```

**Depois:**
```markdown
- [Arquitetura](docs/ARCHITECTURE.md) - Visão completa do sistema
- [API](docs/API.md) - Referência dos endpoints REST
- [Testes](docs/TESTING.md) - Guia de testes e cobertura E2E
- [ADRs](docs/adr/) - Architecture Decision Records
- [PRDs](docs/prd/) - Product Requirements Documents
- [Índice Completo](docs/README.md) - Navegação de toda a documentação
```

#### 3.2.4. Seção "API Endpoints" (linhas 102-104)

Atualizar para listar os endpoints principais:

```markdown
### API Endpoints Principais

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/processos` | Criar processo |
| `GET` | `/api/v1/processos` | Listar processos |
| `POST` | `/api/v1/processos/{id}/configuracoes` | Configurar extração |
| `POST` | `/api/v1/processos/{id}/execucoes` | Iniciar execução |
| `GET` | `/api/v1/execucoes/{id}` | Status da execução |

📖 [Documentação completa da API](docs/API.md)
```

#### 3.2.5. Seção "Testes" (linhas 109-120)

Atualizar para incluir E2E:

```markdown
## 🧪 Testes

```bash
make test              # Testes unitários + integração (cobertura 90%)
make test-e2e          # Testes E2E com Playwright (headless)
make test-e2e-headed   # Testes E2E com browser visível
```

📖 [Guia completo de testes](docs/TESTING.md)
```

---

## 4. Critérios de Aceite

- [ ] Nenhuma menção a Black, isort ou flake8 no README
- [ ] Ruff mencionado como ferramenta de linting/formatação
- [ ] Links para `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/TESTING.md` presentes
- [ ] Nenhum link para diretórios inexistentes (`docs/architecture/`, `docs/api/`)
- [ ] Playwright/E2E mencionados na seção de testes
- [ ] Tabela de endpoints principais com link para doc completa
- [ ] README permanece na raiz do projeto (`./README.md`)

---

## 5. Notas de Implementação

- O README deve permanecer na **raiz do projeto** (`./README.md`)
- Os links para `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/TESTING.md` referenciam arquivos que serão criados pelos PRDs ORG-002, ORG-003 e ORG-004. Os links devem ser criados agora mesmo que os arquivos ainda não existam.
- Manter toda a documentação em **Português (PT-BR)**
- Não alterar seções que já estão corretas (Pré-requisitos, Instalação, Licença, Contribuindo)
