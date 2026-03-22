# PRD-ORG-004: Documento de Testes

**Status**: ✅ Implementado
**Prioridade**: 🟠 Média
**Categoria**: Documentação
**Tipo**: Novo Documento

---

## 1. Objetivo

Criar o documento `docs/TESTING.md` com o guia completo de testes do projeto, incluindo como rodar, estrutura, mapeamento de cobertura E2E, e como adicionar novos testes.

## 2. Contexto e Justificativa

O projeto tem uma suíte robusta de testes (unit, integration, E2E com Playwright), mas não existe documentação que:
- Explique como rodar cada tipo de teste
- Mapeie quais funcionalidades o E2E cobre
- Sirva de referência para identificar gaps de cobertura
- Guie a criação de novos testes

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: D4, T2

---

## 3. Conteúdo Obrigatório

### 3.1. Visão Geral

- Ferramenta: pytest
- Cobertura mínima: 90% (configurado em `pyproject.toml`)
- Modo asyncio: `auto` (todos os testes async rodam automaticamente)

### 3.2. Estrutura de Testes

```
tests/
├── conftest.py          # Fixtures globais (test DB, mocking)
├── unit/                # Testes isolados (sem DB real, sem HTTP)
├── integration/         # Testes com DB e serviços reais
├── e2e/                 # Testes com browser (Playwright)
│   ├── conftest.py      # Fixtures E2E (live_server, page)
│   ├── test_smoke.py
│   ├── test_uc01_*.py   # Casos de uso numerados
│   └── ...
└── fixtures/            # Geradores de dados de teste
```

### 3.3. Como Rodar

Tabela com todos os comandos:

| Comando | O que roda | Tempo estimado |
|---------|-----------|----------------|
| `make test` | Unit + Integration (com cobertura 90%) | ~5s |
| `make test-e2e` | E2E Playwright (headless) | ~30s |
| `make test-e2e-headed` | E2E com browser visível | ~30s |
| `make quality` | Lint + Security + Audit + Testes | ~15s |
| `poetry run pytest tests/unit/` | Apenas unitários | ~2s |
| `poetry run pytest tests/integration/` | Apenas integração | ~3s |
| `poetry run pytest tests/e2e/ -k "uc01"` | E2E específico | ~5s |

### 3.4. Pré-requisitos para E2E

Documentar setup necessário:
```bash
# Instalar browsers do Playwright
playwright install chromium --with-deps

# Serviços necessários (Redis + API rodando)
make docker-up
# OU rodar localmente:
make run  # em um terminal
```

### 3.5. Mapeamento de Cobertura E2E

O agente deve ler **todos** os arquivos em `tests/e2e/` e gerar uma tabela:

| Arquivo | UC | Funcionalidade Testada | Cenários |
|---------|----|-----------------------|----------|
| `test_smoke.py` | — | Health check básico | 1-2 |
| `test_uc01_criar_processo.py` | UC-01 | Criação de processo | N |
| `test_uc02_validacao_formulario.py` | UC-02 | Validação de formulários | N |
| ... | ... | ... | ... |

Para cada arquivo E2E, listar:
- Nome do arquivo
- Caso de uso que cobre
- Descrição do que testa
- Número de cenários/testes

### 3.6. Markers do pytest

Documentar os markers configurados (extrair do `pyproject.toml`):

```
unit        → Testes unitários
integration → Testes de integração
e2e         → Testes end-to-end (Playwright)
slow        → Testes lentos (> 1s)
requires_redis  → Precisa de Redis rodando
requires_celery → Precisa de Celery worker
```

### 3.7. Fixtures Principais

Documentar as fixtures mais importantes de `tests/conftest.py` e `tests/e2e/conftest.py`:
- O que cada fixture fornece
- Escopo (function, session, module)
- Dependências

### 3.8. Como Adicionar Novos Testes

Guia prático:

1. **Teste unitário**: Criar em `tests/unit/`, mockar dependências
2. **Teste de integração**: Criar em `tests/integration/`, usar DB de teste
3. **Teste E2E**: Criar em `tests/e2e/test_ucXX_nome.py`, seguir padrão de UCs
4. **Nomenclatura**: `test_ucNN_descricao.py` para E2E, `test_modulo.py` para unit/integration

### 3.9. Gaps de Cobertura Identificados

Seção para documentar funcionalidades que **não** têm cobertura E2E. O agente deve comparar:
- Funcionalidades do frontend (páginas em `frontend/templates/pages/`)
- Testes E2E existentes (`tests/e2e/`)

E listar o que falta.

---

## 4. Critérios de Aceite

- [ ] Arquivo `docs/TESTING.md` criado
- [ ] Tabela de comandos para rodar testes
- [ ] Mapeamento de todos os arquivos E2E com descrição
- [ ] Guia de pré-requisitos para E2E
- [ ] Markers do pytest documentados
- [ ] Seção de gaps de cobertura
- [ ] Documento em Português (PT-BR)

---

## 5. Fontes de Informação

O agente deve ler:
- `pyproject.toml` → configuração do pytest, markers
- `tests/conftest.py` → fixtures globais
- `tests/e2e/conftest.py` → fixtures E2E
- `tests/e2e/*.py` → todos os arquivos de teste E2E
- `tests/unit/` e `tests/integration/` → estrutura existente
- `frontend/templates/pages/` → páginas do frontend (para gap analysis)
- `Makefile` → comandos de teste
