# ADR-007: Qualidade de Software — Ferramentas e Padrões

**Status**: Aceito
**Data**: 2026-03-04
**Contexto**: Garantir consistência, segurança e confiabilidade do código em um projeto com múltiplos módulos (API, workers assíncronos, extração web, frontend server-side).

---

## Decisão

Adotar um pipeline de qualidade automatizado com as seguintes camadas: **linting, formatação, tipagem estática, segurança e cobertura de testes**, executadas tanto localmente (pre-commit) quanto no CI/CD (GitHub Actions).

---

## Ferramentas Adotadas

### Linting e Formatação

| Ferramenta | Substitui | Função |
|---|---|---|
| **ruff** | `black` + `isort` + `flake8` | Linter + formatter. 10-100x mais rápido. Cobre pycodestyle, pyflakes, bugbear, comprehensions, pyupgrade, simplify, isort |
| **mypy** | — | Verificação estática de tipos. Configurado para produção (`toninho/`) com erros pré-existentes suprimidos explicitamente via `disable_error_code` |

**Conjuntos de regras ruff ativos:**

| Código | Origem | Descrição |
|---|---|---|
| `E`, `W` | pycodestyle | Estilo PEP 8 |
| `F` | pyflakes | Erros de import, variáveis não usadas |
| `I` | isort | Ordenação de imports |
| `B` | flake8-bugbear | Anti-patterns e bugs comuns |
| `C4` | flake8-comprehensions | List/dict comprehensions desnecessárias |
| `UP` | pyupgrade | Modernização da sintaxe (Python 3.11+) |
| `SIM` | flake8-simplify | Simplificação de estruturas condicionais |
| `TCH` | flake8-type-checking | Imports apenas em TYPE_CHECKING blocks |
| `RUF` | ruff-specific | Regras exclusivas do ruff |

### Segurança

| Ferramenta | Função |
|---|---|
| **bandit** | Análise estática de segurança do código Python (OWASP Top 10, CWEs) |
| **pip-audit** | Verifica CVEs conhecidas nas dependências declaradas no `poetry.lock` |

**Regras bandit ignoradas intencionalmente:**

| ID | Motivo |
|---|---|
| `B101` | `assert` em testes é esperado |
| `B110` | `try/except: pass` é padrão intencional em blocos de limpeza |
| `B112` | `try/except: continue` idem |
| `B104` | `0.0.0.0` em `config.py` suprimido via `# nosec B104` — binding configurável via variável `HOST` |
| `B108` | Strings `/tmp/...` em `examples=[]` de campos Pydantic suprimidas via `# nosec B108` — são apenas exemplos de documentação, não operações de arquivo |

### Testes e Cobertura

| Ferramenta | Configuração |
|---|---|
| **pytest** | `testpaths = ["tests"]`, `asyncio_mode = auto` |
| **pytest-cov** | Relatórios: terminal, HTML (`htmlcov/`), XML (`coverage.xml`) |
| **Cobertura mínima** | **90%** — configurado em `--cov-fail-under=90` |

**Tipos de testes suportados:**

```
tests/
├── unit/           # Testes unitários isolados (mocks de dependências externas)
├── integration/    # Testes de integração (FastAPI TestClient + SQLite em memória)
└── e2e/            # Testes ponta a ponta (fluxo completo de extração)
```

---

## Execução Automática

### Pre-commit Hooks (local, a cada `git commit`)

Ordem de execução:

1. `pre-commit-hooks` — trailing whitespace, EOF fixer, YAML/TOML/JSON syntax, large files, private keys, debug statements, mixed line endings
2. `ruff` — lint com auto-fix
3. `ruff-format` — formatação
4. `mypy` — tipagem estática (apenas `toninho/`)
5. `bandit` — segurança
6. `pip-audit` — CVEs em dependências (ativado apenas quando `poetry.lock` ou `pyproject.toml` mudam)

### CI/CD — GitHub Actions (`.github/workflows/ci.yml`)

| Job | Trigger | Conteúdo |
|---|---|---|
| `quality` | push/PR em `main`, `develop` | ruff check + ruff format --check + mypy + bandit + pip-audit |
| `test` | push/PR em `main`, `develop` | pytest com coverage em Python 3.11 e 3.12 (matrix) |

---

## Comandos Makefile

```bash
make format     # ruff format + ruff check --fix (altera arquivos)
make check      # ruff --check + mypy (somente verifica, sem alterar)
make lint       # ruff check + mypy
make security   # bandit
make audit      # pip-audit
make quality    # check + lint + security + audit + test (pipeline completo)
```

---

## Alternativas Rejeitadas

| Alternativa | Motivo rejeição |
|---|---|
| `black` + `isort` + `flake8` separados | Substituídos pelo ruff: mesma funcionalidade, única dependência, 10-100x mais rápido |
| `pylint` | Verboso, lento, alta taxa de falsos positivos para projetos FastAPI/Pydantic |
| Cobertura mínima < 90% | Risco de regressões silenciosas em workers assíncronos e lógica de extração |
| Cobertura mínima 100% | Impraticável para código de I/O e integrações externas (browser, HTTP) sem mocks excessivos |

## Consequências

- Todo `git commit` é validado automaticamente — commits com violações são bloqueados localmente.
- PRs falham no CI se qualquer verificação de qualidade não passar.
- O projeto mantém formatação uniforme sem debates de estilo.
- Novo código com cobertura < 90% bloqueia o pipeline de testes.
- Vulnerabilidades em dependências são detectadas na mudança do `poetry.lock`.
