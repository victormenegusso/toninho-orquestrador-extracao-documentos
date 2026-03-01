# PRD-001: Setup do Projeto

**Status**: 📋 Pronto para implementação  
**Prioridade**: 🔴 Crítica - Bloqueante  
**Categoria**: Setup e Infraestrutura  
**Estimativa**: 4-6 horas

---

## 1. Objetivo

Criar a estrutura inicial do repositório do projeto Toninho com organização de pastas, arquivos de configuração base, documentação inicial e ferramentas de qualidade de código. Este PRD estabelece a fundação sobre a qual todos os demais componentes serão construídos.

## 2. Contexto e Justificativa

O projeto Toninho é um sistema de extração de dados web baseado em Python, utilizando FastAPI como framework principal. A estrutura de pastas seguirá o padrão de arquitetura em camadas (Controller → Service → Repository), facilitando manutenção, testabilidade e escalabilidade.

**Decisões arquiteturais importantes:**
- Monolito modular (backend + frontend no mesmo repositório)
- Separação clara entre camadas (API, Services, Repositories, Models)
- Extensibilidade via interfaces abstratas (Strategy Pattern)
- Single-user, uso local, sem necessidade de autenticação

## 3. Requisitos Técnicos

### 3.1. Estrutura de Diretórios

```
toninho-processo-extracao/
├── toninho/                      # Código fonte principal (package Python)
│   ├── __init__.py              # Marca como pacote Python
│   ├── api/                     # Camada de API (Controllers)
│   │   ├── __init__.py
│   │   ├── routes/              # Endpoints REST
│   │   │   ├── __init__.py
│   │   │   └── README.md        # Convenções de rotas
│   │   └── dependencies/        # Dependency Injection e validações
│   │       ├── __init__.py
│   │       └── README.md
│   ├── services/                # Lógica de negócio
│   │   ├── __init__.py
│   │   └── README.md
│   ├── repositories/            # Acesso a dados (Data Access Layer)
│   │   ├── __init__.py
│   │   └── README.md
│   ├── models/                  # Entidades do domínio (SQLAlchemy)
│   │   ├── __init__.py
│   │   └── README.md
│   ├── schemas/                 # DTOs e validação (Pydantic)
│   │   ├── __init__.py
│   │   └── README.md
│   ├── workers/                 # Celery tasks (processamento assíncrono)
│   │   ├── __init__.py
│   │   └── README.md
│   ├── core/                    # Configurações, constantes, logging
│   │   ├── __init__.py
│   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   ├── logging.py          # Configuração Loguru
│   │   ├── constants.py        # Constantes do sistema
│   │   └── exceptions.py       # Exceções customizadas
│   └── main.py                 # Entry point da aplicação FastAPI
│
├── frontend/                    # Código frontend (HTMX + Alpine.js)
│   ├── static/                  # Arquivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/               # Templates Jinja2
│       ├── base.html
│       ├── components/
│       └── pages/
│
├── tests/                       # Testes automatizados
│   ├── __init__.py
│   ├── unit/                    # Testes unitários
│   │   └── __init__.py
│   ├── integration/             # Testes de integração
│   │   └── __init__.py
│   ├── fixtures/                # Dados e mocks para testes
│   │   └── __init__.py
│   └── conftest.py             # Configurações pytest
│
├── migrations/                  # Alembic migrations
│   └── README.md
│
├── scripts/                     # Scripts utilitários
│   ├── setup.sh                # Setup inicial do ambiente
│   ├── run_dev.sh              # Executar em modo desenvolvimento
│   └── run_tests.sh            # Executar testes
│
├── docs/                        # Documentação do projeto
│   ├── architecture/            # Diagramas e decisões arquiteturais
│   ├── api/                     # Documentação da API
│   └── prd/                     # Product Requirements Documents
│
├── output/                      # Diretório para arquivos extraídos (gitignored)
│   └── .gitkeep
│
├── .github/                     # GitHub específico (CI/CD)
│   └── workflows/
│       └── ci.yml
│
├── .gitignore                   # Arquivos/pastas ignorados pelo git
├── .env.example                 # Template de variáveis de ambiente
├── .editorconfig                # Configuração de editores
├── .pre-commit-config.yaml      # Pre-commit hooks
├── pyproject.toml               # Configuração Poetry + ferramentas
├── README.md                    # Documentação principal
├── LICENSE                      # Licença do projeto
└── Makefile                     # Comandos úteis (make install, make test, etc)
```

### 3.2. Arquivos de Configuração Base

#### `.gitignore`
Deve incluir:
- Ambientes virtuais Python (venv/, env/, .venv/)
- Arquivos compilados Python (\_\_pycache\_\_/, \*.pyc, \*.pyo)
- Banco de dados local (\*.db, \*.sqlite, \*.sqlite3)
- Variáveis de ambiente (.env, .env.local)
- Diretório de output (output/)
- IDEs (\.vscode/, \.idea/, \*.swp)
- Logs (\*.log)
- Cache pytest (.pytest\_cache/)
- Coverage (.coverage, htmlcov/)
- OS específicos (.DS\_Store, Thumbs.db)

#### `.env.example`
Template com todas as variáveis necessárias:
```env
# Servidor
PORT=8000
HOST=0.0.0.0
DEBUG=true
LOG_LEVEL=INFO

# Banco de Dados
DATABASE_URL=sqlite:///./toninho.db

# Redis (Message Broker)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Workers
MAX_CONCURRENT_PROCESSES=5
WORKER_CONCURRENCY=2

# Extração
DEFAULT_TIMEOUT=3600
MAX_RETRIES=3
MAX_SIZE_PER_EXTRACTION=1073741824
OUTPUT_DIR=./output

# Cache
CACHE_HTTP_REQUESTS=true
CACHE_EXPIRATION=3600

# Processamento
PARALLEL_THREADS=4

# Storage
STORAGE_TYPE=local

# Segurança
SECRET_KEY=change-me-in-production
```

#### `.editorconfig`
Garantir consistência entre editores:
```ini
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{yml,yaml,json}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

#### `.pre-commit-config.yaml`
Hooks para garantir qualidade:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ["--ignore-missing-imports"]
```

#### `pyproject.toml`
Configuração centralizada do projeto:
```toml
[tool.poetry]
name = "toninho"
version = "0.1.0"
description = "Agente orquestrador de processos de extração de dados"
authors = ["Seu Nome <seu@email.com>"]
readme = "README.md"
packages = [{include = "toninho"}]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
pydantic = "^2.5.3"
pydantic-settings = "^2.1.0"
celery = "^5.3.6"
redis = "^5.0.1"
httpx = "^0.26.0"
loguru = "^0.7.2"
python-dotenv = "^1.0.1"
jinja2 = "^3.1.3"
python-multipart = "^0.0.6"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
httpx-mock = "^0.11.0"
black = "^23.12.1"
isort = "^5.13.2"
flake8 = "^7.0.0"
mypy = "^1.8.0"
pre-commit = "^3.6.0"
testcontainers = "^3.7.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=toninho --cov-report=html --cov-report=term-missing"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["toninho"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

#### `Makefile`
Comandos úteis para desenvolvedores:
```makefile
.PHONY: help install run test lint format clean

help:
	@echo "Comandos disponíveis:"
	@echo "  make install    - Instala dependências"
	@echo "  make run        - Executa aplicação"
	@echo "  make test       - Executa testes"
	@echo "  make lint       - Executa linters"
	@echo "  make format     - Formata código"
	@echo "  make clean      - Remove arquivos temporários"

install:
	poetry install
	poetry run pre-commit install

run:
	poetry run uvicorn toninho.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest

lint:
	poetry run flake8 toninho tests
	poetry run mypy toninho

format:
	poetry run black toninho tests
	poetry run isort toninho tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov
```

### 3.3. Documentação Inicial

#### `README.md`
Deve conter:
- Descrição do projeto e objetivo
- Características principais
- Pré-requisitos (Python 3.11+, Poetry, Redis, Docker)
- Instruções de instalação (local e Docker)
- Como executar (desenvolvimento e produção)
- Como executar testes
- Estrutura do projeto
- Tecnologias utilizadas
- Convenções de código
- Como contribuir
- Licença
- Links para documentação adicional

#### READMEs por diretório
Cada pasta principal deve ter um README.md explicando:
- **api/routes**: Convenções de rotas, estrutura de endpoints, padrões REST
- **services**: Responsabilidades da camada de serviço, padrões de implementação
- **repositories**: Padrões de acesso a dados, queries comuns
- **models**: Convenções de nomenclatura, relacionamentos
- **schemas**: Padrões de validação Pydantic, DTOs
- **workers**: Como criar tasks Celery, convenções
- **core**: Arquivos de configuração, como adicionar novos settings

### 3.4. Licença

Definir licença apropriada (sugestão: MIT License para projeto de estudo).

### 3.5. Configuração de CI/CD Básica

Arquivo `.github/workflows/ci.yml` com:
- Trigger em push e pull requests para main/develop
- Jobs: lint, test, build
- Matriz de versões Python (3.11, 3.12)
- Upload de coverage reports
- Notificações de falhas

## 4. Dependências

### 4.1. Pré-requisitos
- Git instalado
- Python 3.11+ instalado
- Poetry instalado (gerenciador de dependências)

### 4.2. Dependências de Outros PRDs
**Nenhuma** - Este é o PRD inicial, bloqueante para todos os outros.

### 4.3. PRDs Subsequentes
- PRD-002: Ambiente de Desenvolvimento (depende deste)
- PRD-003: Models e Database (depende deste)
- Todos os demais PRDs dependem indiretamente deste

## 5. Regras de Negócio

### 5.1. Organização de Código
- **Separação de responsabilidades**: Cada camada tem responsabilidade única
- **Convenção de nomenclatura**: snake_case para arquivos/variáveis, PascalCase para classes
- **Imports organizados**: stdlib → third-party → local, ordenados alfabeticamente
- **Type hints**: Obrigatório em todas as funções públicas

### 5.2. Qualidade de Código
- **Coverage mínimo**: 90% de cobertura de testes
- **Linting**: Código deve passar em black, isort, flake8, mypy
- **Pre-commit**: Hooks devem executar antes de cada commit
- **Documentação**: Docstrings obrigatórias em classes e funções públicas

### 5.3. Versionamento
- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Branches**: main (produção), develop (desenvolvimento), feature/* (features)
- **Commits**: Conventional Commits (feat:, fix:, docs:, refactor:, test:, chore:)

## 6. Casos de Teste

### 6.1. Validação de Estrutura
- ✅ Todos os diretórios especificados existem
- ✅ Todos os `__init__.py` estão presentes nos pacotes Python
- ✅ READMEs existem nas pastas principais
- ✅ Arquivos de configuração seguem formato correto

### 6.2. Validação de Ferramentas
- ✅ Poetry resolve dependências sem conflitos
- ✅ Pre-commit hooks estão instalados
- ✅ Black, isort, flake8, mypy executam sem erros
- ✅ Pytest encontra diretório de testes

### 6.3. Validação de Documentação
- ✅ README.md contém todas as seções obrigatórias
- ✅ .env.example contém todas as variáveis necessárias
- ✅ Licença está presente e é válida

## 7. Critérios de Aceitação

### ✅ Estrutura
- [ ] Estrutura completa de diretórios criada
- [ ] Todos os `__init__.py` presentes
- [ ] READMEs em todas as pastas principais

### ✅ Configuração
- [ ] pyproject.toml configurado com todas as dependências
- [ ] .gitignore completo
- [ ] .editorconfig configurado
- [ ] .env.example com todas as variáveis
- [ ] .pre-commit-config.yaml configurado
- [ ] Makefile com comandos úteis

### ✅ Documentação
- [ ] README.md principal completo
- [ ] LICENSE definida
- [ ] READMEs por diretório escritos

### ✅ CI/CD
- [ ] GitHub Actions configurado
- [ ] Pipeline CI básico funcionando

### ✅ Qualidade
- [ ] `poetry install` executa sem erros
- [ ] `make lint` passa sem erros
- [ ] `make format` formata código corretamente
- [ ] Pre-commit hooks instalados e funcionando
- [ ] Git repositório inicializado

## 8. Notas de Implementação

### 8.1. Ordem de Execução Sugerida
1. Inicializar repositório Git
2. Criar estrutura de diretórios completa
3. Criar todos os `__init__.py`
4. Criar pyproject.toml e instalar dependências
5. Criar arquivos de configuração (.gitignore, .editorconfig, etc)
6. Criar Makefile e scripts utilitários
7. Criar README.md principal
8. Criar READMEs por diretório
9. Configurar pre-commit hooks
10. Configurar CI/CD
11. Primeiro commit

### 8.2. Validação Manual
Após implementação, executar:
```bash
# Validar estrutura
tree -L 3 -I '__pycache__|*.pyc'

# Validar Poetry
poetry check
poetry install

# Validar formatação
make format
make lint

# Validar pre-commit
pre-commit run --all-files

# Primeiro commit
git add .
git commit -m "chore: initial project setup"
```

### 8.3. Pontos de Atenção
- **Versão Python**: Garantir Python 3.11+ está instalado
- **Poetry**: Certificar que Poetry está atualizado (1.7+)
- **Git**: Não commitar .env ou arquivos sensíveis
- **Output**: Diretório output/ deve estar no .gitignore
- **Platform**: Scripts .sh podem precisar permissões de execução (chmod +x)

## 9. Referências Técnicas

- **Python Packaging**: https://packaging.python.org/
- **Poetry**: https://python-poetry.org/docs/
- **FastAPI Project Structure**: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- **Pre-commit**: https://pre-commit.com/
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/
- **GitHub Actions**: https://docs.github.com/en/actions

## 10. Definição de Pronto

Este PRD estará completo quando:
- ✅ Estrutura completa de diretórios existe
- ✅ Todos os arquivos de configuração estão criados e validados
- ✅ Poetry instala dependências sem erros
- ✅ Todas as ferramentas de qualidade funcionam (black, isort, flake8, mypy)
- ✅ Pre-commit hooks instalados
- ✅ README.md completo e atualizado
- ✅ CI/CD básico configurado e verde
- ✅ Primeiro commit realizado com sucesso
- ✅ Repositório pode ser clonado e setup executado por outra pessoa sem erros

---

**Próximo PRD**: PRD-002 - Ambiente de Desenvolvimento (Poetry, Docker)
